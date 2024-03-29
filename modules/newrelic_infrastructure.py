import requests
import json
import time
from modules.redis_functions import set_data, get_data
from modules.misc import to_uuid
from modules.config import newrelic_insights_endpoint, newrelic_insights_timeout, newrelic_main_and_insights_keys, newrelic_infrastructure_max_data_age, newrelic_main_api_violation_endpoint, newrelic_main_api_timeout
import logging
logger = logging.getLogger(__name__)

# This module assumes that newrelic insights returns the most recent data first
def get_newrelic_infra_data():
    """
    Collects data for all newrelic infrastructure accounts provided in the
    config file and stores it in redis as json with a key per server with value:
    '[{"orderby": 0, "health_status": "green", "name": "wibble", "summary": {"cpu": 0, "fullest_disk": 0, "disk_io": 0, "memory": 0}}]'
    """
    newrelic_infra_data = {}
    newrelic_infra_data_validity = {}
    newrelic_infra_data_validity['failed_accounts'] = 0
    newrelic_infra_data_validity['total_accounts'] = 0
    newrelic_infra_data_validity['total_checks'] = 0
    for account in newrelic_main_and_insights_keys:
        newrelic_infra_data_validity['total_accounts'] += 1
        number_or_hosts_url = '{}{}/query?nrql=SELECT%20uniqueCount(fullHostname)%20FROM%20SystemSample'.format(newrelic_insights_endpoint, newrelic_main_and_insights_keys[account]['account_number'])
        try:
            number_of_hosts_response = requests.get(number_or_hosts_url, headers={'X-Query-Key': newrelic_main_and_insights_keys[account]['insights_api_key']}, timeout=newrelic_insights_timeout)
            number_of_hosts_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            newrelic_infra_data_validity['failed_accounts'] += 1
            logger.error('Could not get NewRelic Infrastructure data for {} - error getting number of hosts from insights api: Error: {}'.format(account, e))
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
            newrelic_infra_data_validity['failed_accounts'] += 1
            logger.error('Could not get NewRelic Infrastructure data for {}: - error getting metric data from insights api: Error: {}'.format(account, e))
            continue

        account_infra_data = json.loads(metric_data_response.text)
        try:
            violation_data_response = requests.get(newrelic_main_api_violation_endpoint, headers={'X-Api-Key': newrelic_main_and_insights_keys[account]['main_api_key']}, timeout=newrelic_main_api_timeout)
            violation_data_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            newrelic_infra_data_validity['failed_accounts'] += 1
            logger.error('Could not get NewRelic Alerts violation data for {}: - error getting open violation data from main api: Error: {}'.format(account, e))
            continue

        violation_data = json.loads(violation_data_response.text)['violations']
        for num, host_data in enumerate(account_infra_data['results'][0]['events']):
            newrelic_infra_data_validity['total_checks'] += 1
            infrastructure_host = {}
            # name is the display name, if it is not set it is the hostname
            # I will crop the name in the jinja filter
            infrastructure_host['name'] = account_infra_data['results'][0]['events'][num]['fullHostname']
            if account_infra_data['results'][0]['events'][num]['displayName']:
                infrastructure_host['name'] = account_infra_data['results'][0]['events'][num]['displayName']

            # Data older than 5 minutes will be flagged as blue
            # We should move this over to use the "Host Not Reporting"
            # alert data from the section below to determine if a server
            # is not reporting rather than the time it last recoreded
            # data
            timestamp = account_infra_data['results'][0]['events'][num]['timestamp']
            time_accepted_since = ( time.time() - newrelic_infrastructure_max_data_age ) * 1000
            infrastructure_host['orderby'] = 0
            infrastructure_host['health_status'] = 'blue'
            if timestamp > time_accepted_since:
                memory_percentage = None
                if account_infra_data['results'][0]['events'][num]['memoryUsedBytes'] != None and account_infra_data['results'][0]['events'][num]['memoryTotalBytes'] != None:
                    memory_percentage = ( account_infra_data['results'][0]['events'][num]['memoryUsedBytes'] / account_infra_data['results'][0]['events'][num]['memoryTotalBytes'] ) * 100

                infrastructure_host['summary'] = {
                    'memory': 0.0,
                    'disk_io': 0.0,
                    'fullest_disk': 0.0,
                    'cpu': 0.0}

                try:
                    infrastructure_host['summary']['memory'] = float(memory_percentage)
                except (ValueError, TypeError) as e:
                    logger.info("Could not convert memory percentage to float, value '{}' Error: {}".format(memory_percentage, e))
                try:
                    infrastructure_host['summary']['disk_io'] = float(account_infra_data['results'][0]['events'][num]['diskUtilizationPercent'])
                except (ValueError, TypeError) as e:
                    logger.info("Could not convert disk io percentage to float, value '{}' Error: {}".format(account_infra_data['results'][0]['events'][num]['diskUtilizationPercent'], e))
                try:
                    infrastructure_host['summary']['fullest_disk'] = float(account_infra_data['results'][0]['events'][num]['diskUsedPercent'])
                except (ValueError, TypeError) as e:
                    logger.info("Could not convert disk usage percentage to float, value '{}' Error: {}".format(account_infra_data['results'][0]['events'][num]['diskUsedPercent'], e))
                try:
                    infrastructure_host['summary']['cpu'] = float(account_infra_data['results'][0]['events'][num]['cpuPercent'])
                except (ValueError, TypeError) as e:
                    logger.info("Could not convert cpu percentage to float, value '{}' Error: {}".format(account_infra_data['results'][0]['events'][num]['cpuPercent'], e))

                # Setting the orderby using the same field as newrelic servers
                infrastructure_host['orderby'] = max(
                    infrastructure_host['summary']['cpu'],
                    infrastructure_host['summary']['memory'],
                    infrastructure_host['summary']['fullest_disk'],
                    infrastructure_host['summary']['disk_io'])

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
                    try:
                        if infrastructure_host['name'] in violation['entity']['name']:
                            if violation['condition_name'] == 'Host Not Reporting':
                                violation_level = 3
                            elif violation['priority'] == 'Warning':
                                if violation_level < 1:
                                    violation_level = 1
                            elif violation['priority'] == 'Critical':
                                if violation_level < 2:
                                    violation_level = 2
                            else:
                                logger.warning('Unrecognised violation {} expected Warning or Critical'.format(violation['priority']))
                    except:
                        logger.warning('Unrecognised violation bad input data for {}, from {}'.format(account, infrastructure_host))
                        # 24-11-2021 12:56:30: warboard_daemon.modules.newrelic_infrastructure: WARNING: Unrecognised violation bad input data for {'name': None, 'orderby': 49.64794311361705, 'health_status': 'blue', 'summary': {'memory': 49.64794311361705, 'disk_io': 0.2433389169458473, 'fullest_disk': 48.53858019761348, 'cpu': 1.215955413371545}}


                if violation_level == 0:
                    infrastructure_host['health_status'] = 'green'
                elif violation_level == 1:
                    infrastructure_host['health_status'] = 'orange'
                elif violation_level == 2:
                    infrastructure_host['health_status'] = 'red'
                elif violation_level == 3:
                    infrastructure_host['health_status'] = 'blue'

            newrelic_infra_data[infrastructure_host['name']] = infrastructure_host

    # Data will be valid for 5 minutes after the module runs
    newrelic_infra_data_validity['valid_until'] = time.time() * 1000 + 300000
    return newrelic_infra_data, newrelic_infra_data_validity

def store_newrelic_infra_data(newrelic_infra_data, newrelic_infra_data_validity):
    """
    Store data returned by get_newrelic_infra_data in redis as key value pairs
    """
    for host in newrelic_infra_data:
        host_data = newrelic_infra_data[host]
        set_data('resources:newrelic_infrastructure#{}'.format(to_uuid(host)), json.dumps([host_data]))

    set_data('resources_success:newrelic_infrastructure', json.dumps([newrelic_infra_data_validity]))
