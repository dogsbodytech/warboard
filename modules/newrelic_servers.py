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

        for server in json.loads(servers_response.text)['servers']:
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
                    'memory': server['memory'],
                    'disk_io': server['disk_io'],
                    'fullest_disk': server['fullest_disk'],
                    'cpu': server['cpu']}
                nr_servers_host['orderby'] = max(nr_servers_host['summary']['cpu'], nr_servers_host['summary']['memory'], nr_servers_host['summary']['fullest_disk'], nr_servers_host['summary']['disk_io'])

            nr_servers_results['successful_checks'] += 1
            key = 'resources_host:{}'.format(to_uuid(nr_servers_host['name']))
            # Create a list with just the dictionary in and convert it to json
            # to be stored in the redis database
            set_data(key, json.dumps([nr_servers_host]))

    set_data('resources_success_newrelic_servers', json.dumps([nr_servers_results]))

def get_newrelic_servers_data():
    newrelic_results = {}
    for account in newrelic_servers_keys:
        try:
            r = requests.get(newrelic_servers_endpoint, headers={'X-Api-Key': newrelic_servers_keys[account]}, timeout=newrelic_servers_timeout)
            if r.status_code != requests.codes.ok:
                raise requests.exceptions.RequestException
            else:
                newrelic_results[account] = r.text # We need to store this in redis as text and load it as json when we pull it out
        except requests.exceptions.RequestException:
            newrelic_results[account] = None
    return(newrelic_results)

def store_newrelic_servers_results():
    failed_newrelic_servers_accounts = 0
    total_newrelic_servers_accounts = 0
    newrelic_data = get_newrelic_servers_data() # Get all the newrelic checks
    for account in newrelic_data:
        total_newrelic_servers_accounts+=1
        if newrelic_data[account] != None: # Check we actually got some data for a check
            set_data('resources_newrelic_servers_'+account, newrelic_data[account]) # Store it in redis
        else:
            failed_newrelic_servers_accounts +=1
            log_messages('Could not get newrelic servers data for '+account, 'error')
    set_data('resources_total_newrelic_servers_accounts', total_newrelic_servers_accounts)
    set_data('resources_failed_newrelic_servers', failed_newrelic_servers_accounts)

def get_newrelic_servers_results():
    all_results = []
    newrelic_results = {}
    for account in newrelic_servers_keys:
        result_json = json.loads(get_data('resources_newrelic_servers_'+account)) # Pull the NR data from redis load it as json and append to a list
        all_results.append(result_json['servers'])
    newrelic_results['total_newrelic_servers_accounts'] = int(get_data('resources_total_newrelic_servers_accounts'))
    newrelic_results['failed_newrelic_servers_accounts'] = int(get_data('resources_failed_newrelic_servers'))
    newrelic_results['checks'] = chain_results(all_results) # Store all the nr results as 1 chained list
    newrelic_results['total_checks'] = len(newrelic_results['checks'])
    newrelic_results['green'] = 0
    newrelic_results['red'] = 0
    newrelic_results['orange'] = 0
    newrelic_results['blue'] = 0
    for check in newrelic_results['checks']: # Categorize all the checks as up/down and use the highest metric for each item as the thing we order by
        if check['reporting'] == True:
            check['orderby'] = max(check['summary']['cpu'], check['summary']['memory'], check['summary']['fullest_disk'], check['summary']['disk_io'])
            if check['health_status'] == 'green':
                newrelic_results['green'] +=1
            elif check['health_status'] == 'orange':
                newrelic_results['orange'] +=1
            elif check['health_status'] == 'red':
                newrelic_results['red'] +=1
        elif check['reporting'] == False:
            check['orderby'] = 0
            check['health_status'] = 'blue'
            newrelic_results['blue'] +=1
    return(newrelic_results)
