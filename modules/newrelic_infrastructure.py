import requests
import json
import time
from redis_functions import set_data, get_data, delete_data
from misc import log_messages, chain_results, to_uuid
from config import newrelic_insights_endpoint, newrelic_insights_timeout, newrelic_main_and_insights_keys, newrelic_infrastructure_max_data_age, newrelic_main_api_violation_endpoint, newrelic_main_api_timeout

# This module assumes that newrelic insights returns the most recent data first
def store_newrelic_infra_data():
    """
    Collects data for all newrelic infrastructure accounts provided in the
    config file and stores it in redis as json with a key per server with value:
    '[{"orderby": 0, "timestamp": 0, "health_status": "green", "name": "wibble", "summary": {"cpu": 0, "fullest_disk": 0, "disk_io": 0, "memory": 0}}]'
    """
    infra_results = {}
    infra_results['failed_newrelic_infra_accounts'] = 0
    infra_results['total_newrelic_infra_accounts'] = 0
    infra_results['total_checks'] = 0
    infra_results['successful_checks'] = 0
    for account in newrelic_main_and_insights_keys:
        all_server_names = []
        infra_results['total_newrelic_infra_accounts'] += 1
        number_or_hosts_url = '{}{}/query?nrql=SELECT%20uniqueCount(fullHostname)%20FROM%20SystemSample'.format(newrelic_insights_endpoint, newrelic_main_and_insights_keys[account]['account_number'])
        try:
            number_of_hosts_response = requests.get(number_or_hosts_url, headers={'X-Query-Key': newrelic_main_and_insights_keys[account]['insights_api_key']}, timeout=newrelic_insights_timeout)
            number_of_hosts_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            infra_results['failed_newrelic_infra_accounts'] += 1
            log_messages('Could not get NewRelic Infrastructure data for {} - error getting number of hosts from insights api: Error: {}'.format(account, e), 'error')
            continue

        # It may be possible for 3 servers to be found, one of which has not
        # reported for a long time and that when limiting by number of results
        # two responses are recieved for one server, one for another and none
        # for the third, the code doesn't currently check this and I expect it
        # would pass both results through and cause duplicate rows on the
        # warboard
        number_of_hosts_data = json.loads(number_of_hosts_response.text)
        number_of_hosts = number_of_hosts_data['results'][0]['uniqueCount']
        metric_data_url = '{}{}/query?nrql=SELECT%20displayName%2C%20fullHostname%2C%20cpuPercent%2C%20memoryUsedBytes%2C%20memoryTotalBytes%2C%20diskUtilizationPercent%2C%20diskUsedPercent%2C%20timestamp%20FROM%20SystemSample%20LIMIT%20{}'.format(newrelic_insights_endpoint, newrelic_main_and_insights_keys[account]['account_number'], number_of_hosts)
        try:
            metric_data_response = requests.get(metric_data_url, headers={'X-Query-Key': newrelic_main_and_insights_keys[account]['insights_api_key']}, timeout=newrelic_insights_timeout)
            metric_data_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            infra_results['failed_newrelic_infra_accounts'] += 1
            log_messages('Could not get NewRelic Infrastructure data for {}: - error getting metric data from insights api: Error: {}'.format(account, e), 'error')
            continue

        account_infra_data = json.loads(metric_data_response.text)
        try:
            violation_data_response = requests.get(newrelic_main_api_violation_endpoint, headers={'X-Api-Key': newrelic_main_and_insights_keys[account]['main_api_key']}, timeout=newrelic_main_api_timeout)
            violation_data_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            infra_results['failed_newrelic_infra_accounts'] += 1
            log_messages('Could not get NewRelic Alerts violation data for {}: - error getting open violation data from main api: Error: {}'.format(account, e), 'error')
            continue

        violation_data = json.loads(violation_data_response.text)['violations']
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

            # Using violation data to determine the health status of servers
            violation_level = 0
            # violation level 0 is green and no violation
            # violation level 1 is orange and Warning
            # violation level 2 is red and Critical
            # I'm giving it a number to make comparisons easier
            for violation in violation_data:
                if violation['entity']['product'] != 'Infrastructure':
                    continue

                # We have the option to just flag all servers in the account
                # orange or red based on Warning or Critical here
                # This would be a consistantly wrong behavior (the best kind of
                # wrong)
                # The issue is that in my testing servers are using names of
                # '<fullhostname> (/)' why they don't just use <fullhostname>
                # is beyond me, I am unsure on if this tracks display names

                # The best I can do to match check if the server / host we are
                # currently checking was the cause of the violation we are
                # currently looping through
                if infrastructure_host['name'] in violation['entity']['name']:
                    if violation['priority'] == 'Warning':
                        if violation_level < 1:
                            violation_level = 1
                    elif violation['priority'] == 'Critical':
                        if violation_level < 2:
                            violation_level = 2
                    else:
                        # I'm not expecting this to happen and if I make the server red it will confuse people, it would be nice to be able to make servers pink or send emails since I doubt the log will be read
                        log_messages('Warning: unrecognised violation {} expected Warning or Critical'.format(violation['priority']), 'error')

            infrastructure_host['health_status'] = 'blue'
            if violation_level == 0:
                infrastructure_host['health_status'] = 'green'
            elif violation_level == 1:
                infrastructure_host['health_status'] = 'orange'
            elif violation_level == 2:
                infrastructure_host['health_status'] = 'red'

            infra_results['successful_checks'] += 1
            # uuid based on the display name falling back to the fullhostname
            print(infrastructure_host['name'])
            print(type(infrastructure_host['name']))
            key = 'resources_host:{}'.format(to_uuid(infrastructure_host['name']))
            # Create a list with just the dictionary in and convert it to json
            # to be stored in the redis database
            set_data(key, json.dumps([infrastructure_host]))

    set_data('resources_success_newrelic_infrastructure', json.dumps([infra_results]))
