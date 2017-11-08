import requests
import json
import math
import time
import calendar
from redis_functions import set_data, get_data
from misc import log_messages, chain_results, to_uuid
from config import newrelic_servers_keys, newrelic_servers_timeout, newrelic_servers_endpoint

def store_newrelic_servers_data():
    """
    Collects data for all newrelic servers accounts provided in the config file
    and stores it in redis as json with a key per server with value:
    '[{"orderby": 0, "health_status": "green", "name": "wibble", "summary": {"cpu": 0, "fullest_disk": 0, "disk_io": 0, "memory": 0}}]'
    """
    nr_servers_results = {}
    nr_servers_results['failed_newrelic_servers_accounts'] = 0
    nr_servers_results['total_newrelic_servers_accounts'] = 0
    nr_servers_results['total_checks'] = 0
    nr_servers_results['successful_checks'] = 0
    for account in newrelic_servers_keys:
        try:
            nr_servers_response = requests.get(newrelic_servers_endpoint, headers={'X-Api-Key': newrelic_servers_keys[account]}, timeout=newrelic_servers_timeout)
            nr_servers_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            nr_servers_results['failed_newrelic_servers_accounts'] += 1
            log_messages('Could not get NewRelic Servers data for {} - error getting account data from api: Error: {}'.format(account, e), 'error')
            continue

        for server in json.loads(nr_servers_response.text)['servers']:
            nr_servers_host = {}
            # servers returns name and host, if no dispay name is set it returns
            # the host as both name and host
            # I will crop the name in the jinja filter
            nr_servers_host['name'] = server['name']
            # servers which are not reporting have no health_status and no
            # summary of metric data, hence we set them blue with orderby = 0
            nr_servers_host['orderby'] = 0
            nr_servers_host['health_status'] = 'blue'
            if server['reporting'] == True:
                nr_servers_host['health_status'] = server['health_status']
                nr_servers_host['summary'] = {
                    'memory': server['summary']['memory'],
                    'disk_io': server['summary']['disk_io'],
                    'fullest_disk': server['summary']['fullest_disk'],
                    'cpu': server['summary']['cpu']}
                nr_servers_host['orderby'] = max(nr_servers_host['summary']['cpu'], nr_servers_host['summary']['memory'], nr_servers_host['summary']['fullest_disk'], nr_servers_host['summary']['disk_io'])

            nr_servers_results['successful_checks'] += 1
            key = 'resources:newrelic_servers#{}'.format(to_uuid(nr_servers_host['name']))
            # Create a list with just the dictionary in and convert it to json
            # to be stored in the redis database
            set_data(key, json.dumps([nr_servers_host]))

    set_data('resources_success_newrelic_servers', json.dumps([nr_servers_results]))
