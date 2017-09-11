import requests, math, json
from redis_functions import set_data, get_data
from misc import log_messages, chain_results
from config import newrelic_servers_keys, newrelic_servers_timeout, newrelic_servers_endpoint

def get_newrelic_servers_data():
    newrelic_results = {}
    for account in newrelic_keys:
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
    failed_newrelic = 0
    total_accounts = 0
    newrelic_data = get_newrelic_servers_data() # Get all the newrelic checks
    for account in newrelic_data:
        if newrelic_data[account] != None: # Check we actually got some data for a check
            set_data('resources_newrelic_servers_'+account, newrelic_data[account]) # Store it in redis
        else:
            failed_newrelic +=1
            log_messages('Could not get newrelic servers data for '+account, 'error')
        total_accounts+=1
    set_data('resources_total_newrelic_servers_accounts', total_accounts)
    set_data('resources_failed_newrelic_servers', failed_newrelic)

def get_newrelic_servers_results():
    all_results = []
    newrelic_results = {}
    for account in newrelic_servers_keys:
        result_json = json.loads(get_data('resources_newrelic_servers_'+account)) # Pull the NR data from redis load it as json and append to a list
        all_results.append(result_json['servers'])
    newrelic_results['total_newrelic_accounts'] = int(get_data('resources_total_newrelic_servers_accounts'))
    newrelic_results['failed_newrelic'] = int(get_data('resources_failed_newrelic_servers'))
    newrelic_results['checks'] = chain_results(all_results) # Store all the nr results as 1 chained list
    newrelic_results['total_checks'] = len(newrelic_results['checks'])
    newrelic_results['green'] = 0
    newrelic_results['red'] = 0
    newrelic_results['orange'] = 0
    newrelic_results['blue'] = 0
    for check in newrelic_results['checks']: # Categorize all the checks as up/down and use the highest metric for each item as the thing we order by
        check['name'] = check['name'][:30] # Limit newrelic server names to 30 characters to not break the warboard layout
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
