import time
import requests
from config import appbeat_credentials
import logging
logger = logging.getLogger(__name__)

#https://www.appbeat.io/automation/rest-api/getting-started

def get_appbeat_data_for_account(appbeat_key, timeout=20):
    """
    Input AppBeat API key, returns data formatted for the warboard
    """
    r = requests.get('https://www.appbeat.io/API/v1/status', headers = {'Content-Type': 'application/json'}, params = {'secret': appbeat_key}, timeout = timeout)
    r.raise_for_status()
    status_mapping = {  'Good': 'up',
                        'SystemTimeout' : 'down',
                        'UserTimeout' : 'down',
                        'Undefined' : 'paused',
                        'Error': 'down',
                        'RuleMismatch': 'down'}
    # This is actually returning a load of cool timestamps that it would
    # be nice for the warboard to use.
    # Since we want a validity time for all the accounts we would need
    # to choose the oldest time returned here so I'm just going to stick
    # with the previous method
    checks = []
    for service in r.json()['Services']:
        for check in service['Checks']:
            check_data = {}
            check_data['name'] = '{} {}'.format(service['Name'], check['Name'])
            check_data['status'] = 'paused'
            check_data['type'] = 'N/A'
            check_data['lastresponsetime'] = check.get('ResTime', 0)
            if not check['IsPaused']:
                if check['Status'] in status_mapping:
                    check_data['status'] = status_mapping[check['Status']]
                else:
                    logger.warning("AppBeat returned an unknown unknown status '{}' for '{}'".format(check['Status'], check_data['name']))

            # bodge type based on the naming convention.
            # service will identify the site / server
            # name will identify the check type and and additional info
            # such as a specific site or if the check is IPv6
            # the type should be the right most word other than IPv6
            check_type = check['Name'][:]
            check_type = check_type.upper().split()
            if 'IPV6' in check_type:
                check_type.remove('IPV6')

            if check_data and len(check_type[-1]) <= 5:
                check_data['type'] = check_type[-1]

            checks.append(check_data)

    return checks

def get_appbeat_data():
    """
    Get AppBeat data for all accounts in appbeat_credentials
    """
    appbeat_data = []
    appbeat_validity = {}
    appbeat_validity['failed_accounts'] = 0
    appbeat_validity['total_accounts'] = 0
    appbeat_validity['up'] = 0
    appbeat_validity['down'] = 0
    appbeat_validity['paused'] = 0
    for account in appbeat_credentials:
        appbeat_validity['total_accounts'] += 1
        try:
            data = get_appbeat_data_for_account(appbeat_credentials[account])
        except Exception as e:
            logger.error("Could not get data for AppBeat account '{}'".format(account))
            logger.exception(e)
            appbeat_validity['failed_accounts'] += 1
            continue

        for check in data:
            appbeat_data.append(check)
            appbeat_validity[check['status']] += 1

    # Data should be considerd stale after 5 minutes
    appbeat_validity['valid_until'] = time.time() * 1000 + 300000
    return appbeat_data, appbeat_validity
