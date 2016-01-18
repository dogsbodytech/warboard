import requests
from results import set_data, get_data
from misc import log_errors, chain_results
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
    newrelic_data = get_newrelic_data()
    for account in newrelic_data:
        if newrelic_data[account] != None:
            set_data('newrelic_'+account, newrelic_data[account])
        else:
            failed_newrelic +=1
            log_errors('Could not get newrelic data for '+account)
        total_accounts+=1
    set_data('total_newrelic_accounts', total_accounts)
    set_data('failed_newrelic', failed_newrelic)

def get_newrelic_results():
    all_results = []
    newrelic_results = {}
    for account in newrelic_keys:
        all_results.append(get_data('newrelic_'+account))
    newrelic_results['total_newrelic_accounts'] = get_data('total_newrelic_accounts')
    newrelic_results['failed_newrelic'] = get_data('failed_newrelic')
    newrelic_results['checks'] = chain_results(all_results)
    return(newrelic_results)
