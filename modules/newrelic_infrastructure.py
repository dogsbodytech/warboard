import requests
import json
import ast
import time
from redis_functions import set_data, get_data
from misc import log_messages, chain_results
from config import newrelic_insights_endpoint, newrelic_insights_timeout, newrelic_insights_keys, newrelic_infrastructure_max_data_age, newrelic_infrastructure_endpoint, newrelic_insights_timeout, newrelic_infrastructure_keys

# This module assumes that newrelic insights returns the most recent data first

def store_newrelic_infra_data():
    """
    Calls get_infra_data and puts the relavent structured data into redis
    """
    infra_results = {}
    infra_results['red'] = 0
    infra_results['orange'] = 0
    infra_results['green'] = 0
    infra_results['blue'] = 0
    infra_results['failed_newrelic_infra_accounts'] = 0
    infra_results['total_newrelic_infra_accounts'] = 0
    infra_results['total_checks'] = 0
    infra_results['successful_checks'] = 0
    for account in newrelic_insights_keys:
        account_results = []
        infra_results['total_newrelic_infra_accounts'] += 1
        number_or_hosts_url = '{}{}/query?nrql=SELECT%20uniqueCount(fullHostname)%20FROM%20SystemSample'.format(newrelic_insights_endpoint, newrelic_insights_keys[account]['account_number'])
        try:
            number_of_hosts_response = requests.get(number_or_hosts_url, headers={'X-Query-Key': newrelic_insights_keys[account]['api_key']}, timeout=newrelic_insights_timeout)
            number_of_hosts_response.raise_for_status()
        except requests.exceptions.RequestException:
            infra_results['failed_newrelic_infra_accounts'] += 1
            log_messages('Could not get NewRelic Infrastructure data for {} error'.format(account))
            continue

        # It may be possible for 3 servers to be found, one of which has not
        # reported for a long time and that when limiting by number of results
        # two responses are recieved for one server, one for another and none
        # for the third, the code doesn't currently check this and I expect it
        # would pass both results through and cause duplicate rows on the
        # warboard
        number_of_hosts_data = json.loads(number_of_hosts_response.text)
        number_of_hosts = number_of_hosts_data['results'][0]['uniqueCount']
        metric_data_url = '{}{}/query?nrql=SELECT%20displayName%2C%20fullHostname%2C%20cpuPercent%2C%20memoryUsedBytes%2C%20memoryTotalBytes%2C%20diskUtilizationPercent%2C%20diskUsedPercent%2C%20timestamp%20FROM%20SystemSample%20LIMIT%20{}'.format(newrelic_insights_endpoint, newrelic_insights_keys[account]['account_number'], number_of_hosts)
        try:
            metric_data_response = requests.get(metric_data_url, headers={'X-Query-Key': newrelic_insights_keys[account]['api_key']}, timeout=newrelic_insights_timeout)
            metric_data_response.raise_for_status()
        except requests.exceptions.RequestException:
            infra_results['failed_newrelic_infra_accounts'] += 1
            log_messages('Could not get NewRelic Infrastructure data for {} error'.format(account))
            continue

        account_infra_data = json.loads(metric_data_response.text)
        # I reading the docs I want to use https://rpm.newrelic.com/api/explore/alerts_violations/list?only_open=true
        # however the output format has an ID which I can't match to
        # anything I can pull from the insights api and the name is the
        # hostname with (/) appended, which makes no-sence and I don't want
        # to assume is consistant
        #
        # Hence I will be using the infrastructure alerts api to get the
        # alert conditions and ignoring the time that must be exceeded
        # before warning since it would be too complex to implement
        #
        try:
            alerts_data_response = requests.get(newrelic_infrastructure_endpoint, headers={'X-Api-Key': key}, newrelic_infrastructure_timeout)
            alerts_data_response.raise_for_status()
        except requests.exceptions.RequestException:
            infra_results['failed_newrelic_infra_accounts'] += 1
            log_messages('Could not get NewRelic Infrastructure Alerts data for {} error'.format(account))
            continue

        alerts_data = json.loads(alerts_data_response)['data']
        for num, host_data in enumerate(account_infra_data['results'][0]['events']):
            infra_results['total_checks'] += 1
            infrastructure_host = {}
            # name is the display name, if it is not set it is the hostname
            # I will crop the name in the jinja filter
            infrastructure_host['name'] = account_infra_data['results'][0]['events'][num]['fullHostname']
            if account_infra_data['results'][0]['events'][num]['displayName']:
                infrastructure_host['name'] = account_infra_data['results'][0]['events'][num]['displayName']

            # where green == 0, orange == 1 and red == 2, so I can use > to compare
            most_critical_alert = 0
            for alert in alerts_data:
                try:
                    if alert['enabled'] != 'True':
                        continue

                    # Trying to deal with filters is a pain.
                    # If no filters are used then an alert affects all servers
                    # If a filter is used I need to know which servers are
                    # affected by the alert condition.
                    # Currently the easiest most logical filter to add through
                    # the interface is the entityName filter so I will assume
                    # that we and our customers will only ever use this
                    # I am also assuming that entityName and fullHostname are
                    # identical (we can grab entityName name from insights if
                    # needed but I will set that up later)
                    if 'filter' in alert:
                        if account_infra_data['results'][0]['events'][num]['fullHostname'] in
                    if alert['select_value'] == 'cpuPercent':

                    if alert['select_value'] == 'memoryUsedBytes/memoryTotalBytes*100':

                    if alert['select_value'] == 'totalUtilizationPercent':

                    if alert['select_value'] == 'diskUsedPercent':

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
            memory_percentage = None
            if account_infra_data['results'][0]['events'][num]['memoryUsedBytes'] != None and account_infra_data['results'][0]['events'][num]['memoryTotalBytes'] != None:
                memory_percentage = ( account_infra_data['results'][0]['events'][num]['memoryUsedBytes'] / account_infra_data['results'][0]['events'][num]['memoryTotalBytes'] ) * 100

            infrastructure_host['summary'] = {
                'memory': memory_percentage,
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
            if infrastructure_host['orderby'] == None:
                infrastructure_host['orderby'] = 0
                infrastructure_host['health_status'] = 'blue'
                infra_results['blue'] += 1
            else:
                infrastructure_host['health_status'] = 'green'
                infra_results['green'] += 1

            infra_results['successful_checks'] += 1
            account_results.append(infrastructure_host)

        set_data('resources_newrelic_infra_'+account, account_results)

    set_data('resources_success_newrelic_infrastructure', infra_results)

def get_newrelic_infra_results():
    """
    Pulls Infrastructure data from redis and checks for missing hosts/accounts
    and formats it ready to be merged with other resource modules by the calling
    function
    """
    all_infra_checks = []
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
        retrieved_data_time = time.time()
        if account_checks_string == None or account_checks_string == 'None' or type(account_checks_string) != str:
            infra_results['failed_newrelic_infra_accounts'] += 1
            continue

        account_checks_data_list = ast.literal_eval(account_checks_string)
        # the code needs to check the age of the data to make sure it is not old
        # it also needs to check for hosts that have vanished and deal with them
        # they need to be blue with order by 0, it needs the way it is checking
        # this to have a timeout of say a week in redis keys or I need to add a
        # section to the prune keys file

        for host in account_checks_data_list:
            # NewRelic Insights returns the timestamp as milli-seconds since
            # epoch, I am converting everything to seconds
            if retrieved_data_time - ( host['timestamp'] / 1000 ) > newrelic_infrastructure_max_data_age:
                # Set servers that haven't reported within newrelic_infrastructure_max_data_age
                # seconds to blue and orderby to 0
                # The number of each colour should be counted at the end
                # rather than added to as we go since it would be easier to
                # maintain
                infra_results[host['health_status']] -= 1
                infra_results['blue'] += 1
                host['health_status'] = 'blue'
                host['summary']['orderby'] = 0

        all_infra_checks.append(account_checks_data_list)

    infra_results['checks'] = chain_results(all_infra_checks) # Store all the NewRelic Infrastructure results as 1 chained list
    return infra_results
