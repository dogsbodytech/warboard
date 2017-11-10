import requests
import json
import time
from redis_functions import set_data, get_data
from misc import log_messages
from config import influx_read_users, influx_max_data_age, influx_timeout

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

        for database_as_list in list_of_databases:
            # database is the list ["$database_name"], I can't see how the list
            # will have multiple values and would probably rather break than
            # loop through all of the returned values
            database = database_as_list[0]
            try:
                list_of_hosts_response = requests.get(influx_query_api, params={'u': influx_user['influx_user'], 'p': influx_user['influx_pass'], 'db': database, 'q': 'SHOW TAG VALUES FROM "system" WITH KEY = "host"', 'epoch': 'ms'}, timeout=influx_timeout)
                list_of_hosts_response.raise_for_status()
            except requests.exceptions.RequestException as e:
                # This is now a failed check rather than account so we aren't
                # incrementing a variable as successful_checks are counted in at
                # the end.  Since this module will be ran from within a try
                # statement this exception is just in place to allow other
                # checks to be run if this one fails and to produce a more
                # detailed log since this is an expected error.  As opposed to
                # unexpected errors such as influx changing the API, redis
                # issues, configuration file issues and any other unforseen
                # errors.
                log_messages('Could not get TICK data for {} - error listing hosts from Influx database {}: Error: {}'.format(influx_user['influx_user'], database, e), 'error')
                continue

            list_of_hosts = json.loads(list_of_hosts_response.text)['results'][0]['series'][0]['values']
            for host_as_list in list_of_hosts:
                # host is the list ["host", "$hostname"], I'm happy to just grab
                # the second value
                host = host_as_list[1]
                cpu_query = 'SELECT 100 - LAST("usage_idle") FROM "autogen"."cpu" WHERE "host"=\'{}\''.format(host)
                memory_query = 'SELECT LAST("used_percent") FROM "autogen"."mem" WHERE "host"=\'{}\''.format(host)
                fullest_disk_query
                disk_io_query
                metrics_query = '{};{}'.format(cpu_query, memory_query)
                try:
                    metric_data_response = requests.get(influx_query_api, params={'u': influx_user['influx_user'], 'p': influx_user['influx_pass'], 'db': database, 'q': metrics_query, 'epoch': 'ms'}, timeout=influx_timeout)
                    metric_data_response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    log_messages('Could not get TICK data for {} from {} - error getting metric data for host {} from Influx database {}: Error: {}'.format(influx_user['influx_user'], host, database, e), 'error')
                    continue
                print(metric_data_response.text)


                # Calculate orderby

                # When set-up go and get the health_status for now it will be
                # green for all hosts

            # Format the data as required and place into redis
