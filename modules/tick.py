import requests
import json
import time
from redis_functions import set_data
from misc import log_messages, to_uuid
from config import influx_read_users, influx_timeout, influx_database_batch_size

# Note: If two accounts share hosts with the same name this is going to make a mess

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
        # The four metric queries limit data to the last hour but are
        # mostly interested in the most recent data this is because the
        # decision that the query is invalid is made based on timestamp
        # and will ultimately tie into the deadman alerts
        queries['cpu_query'] = 'SELECT 100 - LAST("usage_idle") AS "cpu" FROM "{}"."autogen"."cpu" WHERE time > now() - 1h GROUP BY "host";'
        queries['memory_query'] = 'SELECT LAST("used_percent") AS "memory" FROM "{}"."autogen"."mem" WHERE time > now() - 1h GROUP BY "host";'
        queries['fullest_disk_query'] = 'SELECT MAX("last_used_percent") AS "fullest_disk" FROM (SELECT last("used_percent") AS "last_used_percent" FROM "{}"."autogen"."disk" WHERE time > now() - 1h GROUP BY "path") GROUP BY "host";'
        # I'm not completly sold on using the last minute of data for
        # our rate of change (the GROUP BY time(1m) bit), we could
        # smooth the output by using 5 minutes or taking a moving
        # average.  It depends on if we want the most recent data or
        # a fairly smooth value.  If we did do this we would want to
        # move cpu usage over to a moving average.
        queries['disk_io_query'] = 'SELECT MAX(latest_delta_io) AS "disk_io" FROM (SELECT LAST("delta_io") AS "latest_delta_io" FROM (SELECT derivative(last("io_time"),1ms) * 100 AS "delta_io" FROM "{}"."autogen"."diskio" WHERE time > now() - 1h GROUP BY time(1m)) GROUP BY "name") GROUP BY "host"'
        # We don't have a tag key for memory, at the moment it is the
        # only thing without a tag so it will be seperate
        # We actually want to pull this query from all of time since it
        # gives the most recent alert status however the db isn't going
        # to appreciate that to I'll grab the last 28 days for now
        queries['alert_query'] = 'SELECT LAST("crit_duration") AS "crit_duration_before_alerting", LAST("warn_duration") AS "warn_duration_before_alerting", LAST("emitted") AS "deadman_status" FROM "{}"."autogen"."kapacitor_alerts" WHERE time > now() - 28d GROUP BY "host","cpu","name","path"'
        list_of_queries = []

        # The next two for loops are a little funky, we want to make as
        # few requests to influx as possible whilst keeping the number
        # low enough that we don't go over any timeouts or max request
        # sizes
        for database_as_list in list_of_databases:
            # database is the list ["$database_name"], I can't see how
            # the list will have multiple values and would probably
            # rather break than loop through all of the returned values
            assert len(database_as_list) == 1
            database = database_as_list[0]
            for query in queries:
                list_of_queries.append(queries[query].format(database))

        # Collect in a list incase influx_database_batch_size is not a
        # multipe of the number of queries we are running per server
        batches_response_list = []
        for beginning_of_slice in xrange(0, len(list_of_queries), influx_database_batch_size):
            batch_query = ';'.join(list_of_queries[beginning_of_slice:beginning_of_slice + influx_database_batch_size])
            try:
                metric_data_batch_response = requests.get(influx_query_api, params={'u': influx_user['influx_user'], 'p': influx_user['influx_pass'], 'q': batch_query, 'epoch': 'ms'}, timeout=influx_timeout)
                metric_data_batch_response.raise_for_status()
            except requests.exceptions.RequestException as e:
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

                # Catch kapacitor alert data and set the health status
                # accordingly
                if statement['series'][0]['name'] == "kapacitor_alerts":
                    alerts = {}
                    # We will create two lists and to store the
                    # crit_duration and warn_duration values in when an
                    # alert is a warning it's warn_duration will be an
                    # integer and it's crit_duration will be None, we
                    # will then grab to max to check if something is
                    # alerting since crit duration has value -1 when not
                    # alerting and x when alerting where x is the
                    # kapacitor variable critTime / warnTime
                    for each_measurement_with_an_alerting_status in statement['series']:
                        hostname = each_measurement_with_an_alerting_status['tags']['host']
                        if hostname not in alerts:
                            alerts[hostname] = {}
                            alerts[hostname]['critical'] = [None]
                            alerts[hostname]['warning'] = [None]
                            alerts[hostname]['deadman_alerting'] = False

                        for tag_or_field_position_in_list, tag_or_field in enumerate(each_measurement_with_an_alerting_status['columns']):
                            if tag_or_field == "time":
                                continue
                            elif tag_or_field == "deadman_status":
                                assert len(each_measurement_with_an_alerting_status['values']) == 1
                                # Checking if a deadman alert is up or
                                # down isn't particularly clear.  We are
                                # working on the basis that when the
                                # latest value is 0 the server is down
                                # and that any other value means the
                                # server is reporting.  In my testing
                                # this seems to be true for every alert
                                # aside from the first one sent by a
                                # each host.
                                if each_measurement_with_an_alerting_status['values'][0][tag_or_field_position_in_list] == 0:
                                    alerts[hostname]['deadman_alerting'] = True
                            elif tag_or_field == "crit_duration_before_alerting":
                                assert len(each_measurement_with_an_alerting_status['values']) == 1
                                alerts[hostname]['critical'].append(each_measurement_with_an_alerting_status['values'][0][tag_or_field_position_in_list])
                            elif tag_or_field == "warn_duration_before_alerting":
                                assert len(each_measurement_with_an_alerting_status['values']) == 1
                                alerts[hostname]['warning'].append(each_measurement_with_an_alerting_status['values'][0][tag_or_field_position_in_list])
                            else:
                                log_messages('Unexpected tag or field when parsing kapacitor alerts for host \'{}\': {}'.format(hostname, tag_or_field), 'warning')

                    for hostname in alerts:
                        health_status = 'green'

                        if max(alerts[hostname]['warning']) > 0:
                            health_status = 'orange'

                        if max(alerts[hostname]['critical']) > 0:
                            health_status = 'red'

                        if alerts[hostname]['deadman_alerting']:
                            health_status = 'blue'

                        # Deadman into influx alerts are causing some
                        # data to be added to influx without a hostname
                        # until this can be debugged the best place to
                        # filter them out seems to be here by having
                        # them never leave the alerts dict to become a
                        # part of the hosts_data dict
                        if hostname not in hosts_data:
                            if len(hostname) == 0:
                                continue

                            tick_data_validity['total_checks'] += 1
                            hosts_data[hostname] = {}
                            hosts_data[hostname]['name'] = hostname

                        hosts_data[hostname]['health_status'] = health_status

                # for all other data - cpu memory disk diskio
                else:
                    for host_data in statement['series']:
                        hostname = host_data['tags']['host']
                        if hostname not in hosts_data:
                            tick_data_validity['total_checks'] += 1
                            hosts_data[hostname] = {}
                            hosts_data[hostname]['name'] = hostname

                        if 'summary' not in hosts_data[hostname]:
                            hosts_data[hostname]['summary'] = {}

                        # cpu and fullest_disk will be the first non time
                        # column
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
            except KeyError as e:
                log_messages('{} did not return data for all metrics, the first missing metric was {}'.format(host, e), 'warning')
                tick_host_data['orderby'] = 0
                tick_host_data['health_status'] = 'blue'

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
