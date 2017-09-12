import requests
import json
import ast
from redis_functions import set_data, get_data
from misc import log_messages, chain_results
from config import newrelic_insights_endpoint, newrelic_insights_timeout, newrelic_insights_keys

def store_newrelic_infra_data():
    """
    Calls get_infra_data and puts the relavent structured data into redis
    """
    infra_results = {}
    infra_results['red'] = 0
    infra_results['orange'] = 0
    infra_results['green'] = 0
    infra_results['blue'] = 0
    infra_results['failed_infa_accounts'] = 0
    infra_results['total_infa_accounts'] = 0
    infra_results['total_checks'] = 0
    infra_results['successful_checks'] = 0
    for account in newrelic_insights_keys:
        account_results = []
        infra_results['total_infa_accounts'] += 1
        number_or_hosts_url = '{}{}/query?nrql=SELECT%20uniqueCount(fullHostname)%20FROM%20SystemSample'.format(newrelic_insights_endpoint, newrelic_insights_keys[account]['account_number'])
        try:
            r = requests.get(number_or_hosts_url, headers={'X-Query-Key': newrelic_insights_keys[account]['api_key']}, timeout=newrelic_insights_timeout)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            infra_results['failed_infa_accounts'] += 1
            log_messages('Could not get NewRelic Infrastructure data for {} error'.format(account))
            continue

        number_of_hosts_data = json.loads(r.text)
        number_of_hosts = number_of_hosts_data['results'][0]['uniqueCount']
        metric_data_url = '{}{}/query?nrql=SELECT%20displayName%2C%20fullHostname%2C%20cpuPercent%2C%20memoryUsedBytes%2C%20memoryTotalBytes%2C%20diskUtilizationPercent%2C%20diskUsedPercent%2C%20timestamp%20FROM%20SystemSample%20LIMIT%20{}'.format(newrelic_insights_endpoint, newrelic_insights_keys[account]['account_number'], number_of_hosts)
        try:
            r = requests.get(metric_data_url, headers={'X-Query-Key': newrelic_insights_keys[account]['api_key']}, timeout=newrelic_insights_timeout)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            infra_results['failed_infa_accounts'] += 1
            log_messages('Could not get NewRelic Infrastructure data for {} error'.format(account))
            continue

        account_infra_data = json.loads(r.text)
        for num, host_data in enumerate(account_infra_data['results'][0]['events']):
            infra_results['total_checks'] += 1
            infrastructure_host = {}
            # name is the display name, if it is not set it is the hostname
            # I will crop the name in the jinja filter
            infrastructure_host['name'] = account_infra_data['results'][0]['events'][num]['fullHostname']
            if account_infra_data['results'][0]['events'][num]['displayName']:
                infrastructure_host['name'] = account_infra_data['results'][0]['events'][num]['displayName']

            # The warboard script will check this was in the last 5 minutes
            # and react acordingly - set to blue order by 0
            # It will make it's own api call to avoid using different timezones
            # and converting from how newrelic want to format the time
            infrastructure_host['timestamp'] = account_infra_data['results'][0]['events'][num]['timestamp']
            # The warboard will need to have a list of hosts and check if they
            # are no-longer present since this will be overwriting the key in
            # redis when it gets a response for half of the hosts/accounts

            # data we are interested in needs to be in a format similar to
            # newrelic servers in order to easily be displayed along side it
            infrastructure_host['summary'] = {
                'memory': ( account_infra_data['results'][0]['events'][num]['memoryUsedBytes'] / account_infra_data['results'][0]['events'][num]['memoryTotalBytes'] ) * 100,
                'disk_io': account_infra_data['results'][0]['events'][num]['diskUtilizationPercent'],
                'fullest_disk': account_infra_data['results'][0]['events'][num]['diskUsedPercent'],
                'cpu': account_infra_data['results'][0]['events'][num]['cpuPercent'] }

            # The warboard script will check this was in the last 5 minutes
            # and react acordingly - set to blue order by 0
            # The warboard will need to have a list of hosts and check if they
            # are no-longer present since this will be overwriting the key in
            # redis when it gets a response for half of the hosts/accounts

            # Setting the orderby using the same field as newrelic servers
            infrastructure_host['orderby'] = max(
                    infrastructure_host['summary']['cpu'],
                    infrastructure_host['summary']['memory'],
                    infrastructure_host['summary']['fullest_disk'],
                    infrastructure_host['summary']['disk_io'])

            # Servers returns this, I can't see how to get it out of the
            # insights api to check if a server has exceeded warning and alert
            # thresholds we could make a call to the infrastructure api
            # however this is not a priority, for now all health_status's
            # are set based on order by where > 80 is red and > 60 is orange
            # this is disabled since we don't want it
            if infrastructure_host['orderby'] > 100:
                infrastructure_host['health_status'] = 'red'
                infra_results['red'] += 1
            elif infrastructure_host['orderby'] > 100:
                infrastructure_host['health_status'] = 'orange'
                infra_results['orange'] += 1
            elif infrastructure_host['orderby'] == 0:
                infrastructure_host['health_status'] = 'blue'
                infra_results['blue'] += 1
            else:
                infrastructure_host['health_status'] = 'green'
                infra_results['green'] += 1

            infra_results['successful_checks'] += 1
            json_infrastructure_host = json.dumps(infrastructure_host)
            account_results.append(json_infrastructure_host)

        set_data('resources_newrelic_infra_'+account, account_results)

    set_data('resources_success_newrelic_infrastructure', infra_results)

def get_newrelic_infra_results():
    """
    Pulls Infrastructure data from redis and checks for missing hosts/accounts
    and formats it ready to be merged with other resource modules by the calling
    function
    """
    all_infra_results = []
    infra_results_string = get_data('resources_success_newrelic_infrastructure')
    # Not going to check resources_success_newrelic_infrastructure is present
    # because if it isn't then we have a bigger problem, I want to put some
    # error handling higher up so that when say infrastructure of sirportly
    # is broken it alerts you but displays a big warning, for now I'll leave
    # this as causing a 500 error since any other unseen issues will also do
    infra_results = ast.literal_eval(infra_results_string)
    for account in newrelic_insights_keys:
        # I need to retrieve the list differently or store it dirrerently
        account_checks_string = get_data('resources_newrelic_infra_{}'.format(account))
        if account_checks_string == None or account_checks_string == 'None' or type(account_checks_string) != str:
            infra_results['failed_infa_accounts'] += 1
            continue

        account_checks_data_list = ast.literal_eval(account_checks_string)
        # the code needs to check the age of the data to make sure it is not old
        # it also needs to check for hosts that have vanished and deal with them
        # they need to be blue with order by 0, it needs the way it is checking
        # this to have a timeout of say a week in redis keys or I need to add a
        # section to the prune keys file
        all_infra_results.append(account_checks_data_list)

    infra_results['checks'] = chain_results(all_infra_results) # Store all the NewRelic Infrastructure results as 1 chained list
    return infra_results
