import requests, math, json
from redis_functions import set_data, get_data
from misc import log_messages, chain_results
from config import newrelic_keys, newrelic_timeout, newrelic_endpoint

def get_newrelic_data():
    newrelic_results = {}
    for account in newrelic_keys:
        try:
            r = requests.get(newrelic_endpoint, headers={'X-Api-Key': newrelic_keys[account]}, timeout=newrelic_timeout)
            if r.status_code != requests.codes.ok:
                raise requests.exceptions.RequestException
            else:
                newrelic_results[account] = r.text # We need to store this in redis as text and load it as json when we pull it out
        except requests.exceptions.RequestException:
            newrelic_results[account] = None
    return(newrelic_results)

def store_newrelic_results():
    failed_newrelic = 0
    total_accounts = 0
    newrelic_data = get_newrelic_data() # Get all the newrelic checks
    for account in newrelic_data:
        if newrelic_data[account] != None: # Check we actually got some data for a check
            set_data('newrelic_'+account, newrelic_data[account]) # Store it in redis
        else:
            failed_newrelic +=1
            log_messages('Could not get newrelic data for '+account, 'error')
        total_accounts+=1
    set_data('total_newrelic_accounts', total_accounts)
    set_data('failed_newrelic', failed_newrelic)

def get_newrelic_results():
    all_results = []
    newrelic_results = {}
    for account in newrelic_keys:
        result_json = json.loads(get_data('newrelic_'+account)) # Pull the NR data from redis load it as json and append to a list
        all_results.append(result_json['servers'])
    newrelic_results['total_newrelic_accounts'] = get_data('total_newrelic_accounts')
    newrelic_results['failed_newrelic'] = int(get_data('failed_newrelic'))
    newrelic_results['working_newrelic'] = int(newrelic_results['total_newrelic_accounts'])-int(newrelic_results['failed_newrelic'])
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
    newrelic_results['red_percent'] = math.ceil(100*float(newrelic_results['red'])/float(newrelic_results['total_checks']))
    newrelic_results['green_percent'] = math.ceil(100*float(newrelic_results['green'])/float(newrelic_results['total_checks']))
    newrelic_results['orange_percent'] = math.ceil(100*float(newrelic_results['orange'])/float(newrelic_results['total_checks']))
    newrelic_results['blue_percent'] = 100-newrelic_results['red_percent']-newrelic_results['green_percent']-newrelic_results['orange_percent']
    if newrelic_results['blue_percent'] < 0:
        newrelic_results['green_percent'] = newrelic_results['green_percent']-abs(newrelic_results['blue_percent'])
    return(newrelic_results)
