import requests
import json
import time
from redis_functions import set_data, get_data
from misc import log_messages
from config import influx_read_users, influx_max_data_age, influx_timeout, influx_database_batch_size

def store_tick_data():
    """
    Collects data for all newrelic infrastructure accounts provided in the
    config file and stores it in redis as json with a key per server with value:
    '[{"orderby": 0, "health_status": "green", "name": "wibble", "summary": {"cpu": 0, "fullest_disk": 0, "disk_io": 0, "memory": 0}}]'
    """
    tick_results = {}
    # This module is written with the assumption that you only have one
    # influx instance to get data from and that the user reading from that
    # instance will have read permissions to every database that is to be
    # displayed from.
    tick_results['failed_accounts'] = 0
    tick_results['total_accounts'] = 0
    tick_results['total_checks'] = 0
    tick_results['successful_checks'] = 0
    for influx_user in influx_read_users:
        influx_query_api = '{}/query'.format(influx_user['influx_url'])
        try:
            list_of_databases_response = requests.get(influx_query_api, params={'u': influx_user['influx_user'], 'p': influx_user['influx_pass'], 'q': 'SHOW DATABASES', 'epoch': 'ms'}, timeout=influx_timeout)
            list_of_databases_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            tick_results['failed_accounts'] += 1
            log_messages('Could not get TICK data for {} - error listing databases from Influx: Error: {}'.format(influx_user['influx_user'], e), 'error')
            continue

        try:
            list_of_databases = json.loads(list_of_databases_response.text)['results'][0]['series'][0]['values']
        except Exception as e:
            tick_results['failed_accounts'] += 1
            log_messages('Could not parse TICK data for {}: Error: {}'.format(influx_user['influx_user'], e), 'error')

        queries = {}
        queries['cpu_query'] = 'SELECT 100 - LAST("usage_idle") AS "cpu" FROM "{}"."autogen"."cpu" GROUP BY "host";'
        queries['memory_query'] = 'SELECT LAST("used_percent") AS "memory" FROM "{}"."autogen"."mem" GROUP BY "host";'
        queries['fullest_disk_query'] = 'SELECT MAX("last_used_percent") AS "fullest_disk" FROM (SELECT last("used_percent") AS "last_used_percent" FROM "{}"."autogen"."disk" GROUP BY "path") GROUP BY "host";'
        # This IO query is probably not using the right time period, I will leave it for now and come back
        queries['disk_io_query'] = 'SELECT LAST("derivative") AS "disk_io" FROM (SELECT derivative(last("io_time"),1ms) FROM "{}"."autogen"."diskio" WHERE time >= 0s GROUP BY time(15m)) GROUP BY "host"'
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

        hosts = {}
        for batch in batches_response_list:
            for statement in batch:
                for host_data in statement['series']:
                    hosts[host_data['tags']['host']] = {}
                    # Check if we have old data
                    if host_data['values'][0][0] < time_accepted_since:
                        hosts[host_data['tags']['host']]['health_status'] = 'blue'
                        # No point storing old data since we don't get it from
                        # servers module
                        continue
                    # cpu and fullest_disk will be the first non time column
                    # create the dictionary hosts[$hostname]['summary']['cpu'] = $cpu_value
                    hosts[host_data['tags']['host']['summary']host_data['columns'][1]] = hosts[host_data['tags']['host']][host_data['values'][0][1]]

        return hosts

        # Calculate orderby

        # When set-up go and get the health_status for now it will be
        # green for all hosts

        # Format the data as required and place into redis
