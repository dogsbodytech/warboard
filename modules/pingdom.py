import requests
import base64
import time
from modules.config import pingdom_keys, pingdom_multiaccounts, pingdom_endpoint, pingdom_timeout
import logging
logger = logging.getLogger(__name__)

def get_pingdom_data():
    pingdom_data = []
    pingdom_validity = {}
    pingdom_validity['failed_accounts'] = 0
    pingdom_validity['total_accounts'] = 0
    pingdom_validity['up'] = 0
    pingdom_validity['down'] = 0
    pingdom_validity['paused'] = 0
    for account in pingdom_keys:
        pingdom_validity['total_accounts'] += 1
        for key in pingdom_keys[account]:
            auth = pingdom_keys[account][key]
            call_headers = {'App-Key': key, 'Authorization': 'Basic {}'.format(base64.b64encode(auth.encode('utf-8')).decode('utf-8'))}
            if account in pingdom_multiaccounts:
                email = pingdom_multiaccounts[account][key]
                call_headers['Account-Email'] = email

            try:
                r = requests.get(pingdom_endpoint, headers=call_headers, timeout=pingdom_timeout)
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error("Could not get pingdom data for '{}' the following error occurred: {}".format(account, e))
                pingdom_validity['failed_accounts'] +=1
                continue

            for check in r.json()['checks']:
                check_data = {}
                check_data['name'] = check['name']
                check_data['lastresponsetime'] = check.get('lastresponsetime', 0)
                check_data['type'] = check['type']
                if check_data['type'] == 'httpcustom':
                    check_data['type'] = 'custom'

                if check['status'] in ('up', 'down', 'paused'):
                    check_data['status'] = check['status']
                else:
                    check_data['status'] = 'paused'
                    if check['status'] not in ('unknown', 'unconfirmed_down'):
                        logger.warning("Pingdom returned an unknown unknown status '{}' for '{}'".format(check['status'], check_data['name']))

                pingdom_validity[check_data['status']] += 1
                pingdom_data.append(check_data)

    # Data should be considerd stale after 5 minutes
    pingdom_validity['valid_until'] = time.time() * 1000 + 300000
    return pingdom_data, pingdom_validity
