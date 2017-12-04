import requests
import json
import time
from redis_functions import set_data, get_data
from misc import log_messages, to_uuid
from config import influx_read_users, influx_max_data_age, influx_timeout, influx_database_batch_size

def get_tick_data():
    """
    Collects data for all influx users provided in the config file and returns
    it as a tuple, dictionary containing all servers as key server name, value
    server data and dictionary with meta data for checks returned
    """
    tick_data = {}
    tick_data_validity = {}
    tick_data_validity['failed_accounts'] = 0
    tick_data_validity['total_accounts'] = 0
    tick_data_validity['total_checks'] = 0
    tick_data_validity['successful_checks'] = 0
    for influx_user in influx_read_users:
        tick_data_validity['total_accounts'] += 1
        influx_query_api = '{}/query'.format(influx_user['influx_url'])
        try:
            list_of_databases_response = requests.get(influx_query_api, params={'u': influx_user['influx_user'], 'p': influx_user['influx_pass'], 'q': 'SHOW DATABASES', 'epoch': 'ms'}, timeout=influx_timeout)
            list_of_databases_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            tick_data_validity['failed_accounts'] += 1
            log_messages('Could not get TICK data for {} - error listing databases from Influx: Error: {}'.format(influx_user['influx_user'], e), 'error')
            continue

        try:
            list_of_databases = json.loads(list_of_databases_response.text)['results'][0]['series'][0]['values']
        except Exception as e:
            tick_data_validity['failed_accounts'] += 1
            log_messages('Could not parse TICK data for {}: Error: {}'.format(influx_user['influx_user'], e), 'error')

        queries = {}
        queries['cpu_query'] = 'SELECT 100 - LAST("usage_idle") AS "cpu" FROM "{}"."autogen"."cpu" WHERE time > now() - 1h GROUP BY "host";'
        queries['memory_query'] = 'SELECT LAST("used_percent") AS "memory" FROM "{}"."autogen"."mem" WHERE time > now() - 1h GROUP BY "host";'
        queries['fullest_disk_query'] = 'SELECT MAX("last_used_percent") AS "fullest_disk" FROM (SELECT last("used_percent") AS "last_used_percent" FROM "{}"."autogen"."disk" WHERE time > now() - 1h GROUP BY "path") GROUP BY "host";'
        # I'm not sure the io time is the best way to calculate disk io
        queries['disk_io_query'] = 'SELECT MAX(latest_delta_io) AS "disk_io" FROM (SELECT LAST("delta_io") AS "latest_delta_io" FROM (SELECT derivative(last("io_time"),100ms) AS "delta_io" FROM "{}"."autogen"."diskio" WHERE time > now() - 1h GROUP BY time(1m)) GROUP BY "name") GROUP BY "host"'
        queries['alert_query'] = 'SELECT LAST("crit_duration") AS "duration_before_alerting" FROM "{}"."autogen"."kapacitor_alerts" WHERE time > now() - 1h GROUP BY "host","kapacitor_alert_level","cpu","total","name","device"'
        list_of_queries = []

        # The next two for loops are a little funky, we want to make as few
        # requests to influx as possible whilst keeping the number low enough
        # that we don't go over any timeouts or max request sizes
        for database_as_list in list_of_databases:
            # database is the list ["$database_name"], I can't see how the list
            # will have multiple values and would probably rather break than
            # loop through all of the returned values
            database = database_as_list[0]
            for query in queries:
                list_of_queries.append(queries[query].format(database))

        # Collect in a list incase influx_database_batch_size is not a multipe
        # of the number of queries we are running per server
        batches_response_list = []
        time_accepted_since = ( time.time() - influx_max_data_age ) * 1000
        for beginning_of_slice in xrange(0, len(list_of_queries), influx_database_batch_size):
            batch_query = ';'.join(list_of_queries[beginning_of_slice:beginning_of_slice + influx_database_batch_size])
            try:
                metric_data_batch_response = requests.get(influx_query_api, params={'u': influx_user['influx_user'], 'p': influx_user['influx_pass'], 'q': batch_query, 'epoch': 'ms'}, timeout=influx_timeout)
                metric_data_batch_response.raise_for_status()
            except requests.exceptions.RequestException as e:
                # This is now a failed batch rather than account, incrementing
                # failed accounts here could cause the output to be
                # misinterpreted.  Failed checks will still be picked up by
                # their absence from successful_checks.
                log_messages('Could not get TICK data for {} - error getting batch of data from Influx: Error: {}'.format(influx_user['influx_user'], e), 'error')
                continue

            try:
                batches_response_list.append(json.loads(metric_data_batch_response.text)['results'])
            except:
                log_messages('Could parse get TICK data for {} - error parsing data recieved from Influx: Error: {}'.format(influx_user['influx_user'], e), 'error')

        # Key = hostname, Value = data
        hosts_data = {}
        for batch in batches_response_list:
            for statement in batch:
                # If we don't get data back there will be no series
                if 'series' not in statement:
                    continue

                # Catch kapacitor alert data and set the health status accordingly
                if statement['series'][0]['name'] == "kapacitor_alerts":
                    alerts = {}
                    alerts['critical'] = [-1]
                    alerts['warning'] = [-1]
                    hostname = statement['series'][0]['tags']['host']
                    for alert in statement['series']:
                        alerts[alert['tags']['kapacitor_alert_level']].append(alert['values'][0][1])

                    health_status = 'green'

                    if max(alerts['warning']) > 0:
                        health_status = 'orange'

                    if max(alerts['critical']) > 0:
                        health_status = 'red'

                    if hostname not in hosts_data:
                        tick_data_validity['total_checks'] += 1
                        hosts_data[hostname] = {}
                        hosts_data[hostname]['name'] = hostname

                    hosts_data[hostname]['health_status'] = health_status
                    continue

                # for all other data - cpu memory disk diskio
                for host_data in statement['series']:
                    hostname = host_data['tags']['host']
                    if hostname not in hosts_data:
                        tick_data_validity['total_checks'] += 1
                        hosts_data[hostname] = {}
                        hosts_data[hostname]['name'] = hostname

                    # Check if we have old data
                    if host_data['values'][0][0] < time_accepted_since:
                        # No point storing old data since we don't store old
                        # data from the servers module
                        continue
                    if 'summary' not in hosts_data[hostname]:
                        hosts_data[hostname]['summary'] = {}

                    # cpu and fullest_disk will be the first non time column
                    hosts_data[hostname]['summary'][host_data['columns'][1]] = host_data['values'][0][1]

        for host in hosts_data:
            tick_host_data = hosts_data[host]
            if 'health_status' not in tick_host_data:
                tick_host_data['health_status'] = 'green'

            try:
                tick_host_data['orderby'] = max(
                    tick_host_data['summary']['cpu'],
                    tick_host_data['summary']['memory'],
                    tick_host_data['summary']['fullest_disk'],
                    tick_host_data['summary']['disk_io'])
            except KeyError:
                tick_host_data['orderby'] = 0
                tick_host_data['health_status'] = 'blue'

            tick_data_validity['successful_checks'] += 1
            tick_data[tick_host_data['name']] = tick_host_data

    tick_data_validity['valid_until'] = time.time() * 1000 + 300000
    return tick_data, tick_data_validity

def store_tick_data(tick_data, tick_data_validity):
    """
    Store data returned by get_tick_data in redis as key value pairs
    """
    for host in tick_data:
        host_data = tick_data[host]
        set_data('resources:tick#{}'.format(to_uuid(host)), json.dumps([host_data]))

    set_data('resources_success:tick', json.dumps([tick_data_validity]))
