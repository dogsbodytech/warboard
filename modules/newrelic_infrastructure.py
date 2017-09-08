import requests
import json
from misc import log_messages, chain_results
from config import insights_endpoint, infra_query, insights_timeout, insights_keys

# this has a lot of shared code with the newrelic module, they could have
# a common library but that would be more work than typing some of it out again

def get_newrelic_infra_data():
    """
    Queries the NR Insights API to get Infrastructure data
    """
    infra_results = {}
    for account in insights_keys:
        url = '{}{}{}'.format(insights_endpoint, insights_keys[account]['account_number'], infra_query)
        infra_results[account] = None
        try:
            r = requests.get(url, headers={'X-Api-Key': insights_keys[account]['api_key']}, timeout=insights_timeout)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            # probably worth logging this
            # (the store_infra_data function seems to be)
            pass
        else:
            infra_results[account] = r.text

    return infra_results

def store_newrelic_infra_data():
    """
    Calls get_infra_data and puts the relavent structured data into redis
    """
    failed_infra = 0
    total_infra_accounts = 0
    infra_data = get_infra_data()
    for account in infra_data:
        # if the get_infra_data function fails it sets the data to None
        if infra_data[account] != None:
            # store the data in redis
            set_data('infra_{}'.format(account), infra_data[account])
        else:
            failed_infra += 1
            log_messages('Could not get NewRelic Infrastructure data for {} error'.format(account))

        total_infra_accounts += 1

    set_data('total_infra_accounts', total_infra_accounts)
    set_data('failed_infra', failed_infra)

def get_newrelic_infra_results():
    """
    Pulls Infrastructure data from redis and formats it to be displayed
    """
    all_infra_results = []
    infra_results = {}
    for account in insights_keys:
        result_json = json.loads(get_data('infra_{}'.format(account)))
        all_infra_results.append(result_json)

    infra_results['total_infra_accounts'] = int(get_data('total_infra_accounts'))
    infra_results['failed_infra'] = int(get_data('failed_infra'))
    infra_results['working_infra'] = infra_results['total_infra_accounts']-infra_results['failed_infra']
    infra_results['working_percentage'] = int(float(infra_results['working_infra'])/float(infra_results['total_infra_accounts'])*100)
    infra_results['checks'] = chain_results(all_results) # Store all the NewRelic Infrastructure results as 1 chained list
    infra_results['total_checks'] = len(infra_results['checks'])
    infra_results['green'] = 0
    infra_results['red'] = 0
    infra_results['orange'] = 0
    infra_results['blue'] = 0
    for customer in infra_results['checks']: # Categorize all the checks as up/down and use the highest metric for each item as the thing we order by
        for server in customer['results'][0]['events']:
            name = server['fullHostname']
            if server['displayName'] != None:
                name = server['displayName']

            name = name[:30] # Limit NewRelic Infrastructure server names to 30 characters to not break the warboard layout
            # not sure how this is handeling servers that are not reporting
            #####I am leaving this here for a minute
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
