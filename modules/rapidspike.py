import hashlib
import hmac
import base64
import time
import requests
from config import rapidspike_credentials
import logging
logger = logging.getLogger(__name__)

# https://docs.rapidspike.com/system-api/index.html

def rapidspike_api_call(uri, public_key, private_key):
    """
    Input the uri to access and credentials, returns the response as
    json
    """
    now = int(time.time())
    # https://docs.rapidspike.com/system-api/authentication.html
    signature = base64.b64encode(hmac.new(private_key.encode(), '{}\n{}'.format(public_key, now).encode(), hashlib.sha1).digest())
    r = requests.get('https://api.rapidspike.com{}'.format(uri), params={'public_key': public_key, 'time': now, 'signature': signature}, timeout=20)
    logging.debug(r.text)
    r.raise_for_status()
    json = r.json()
    assert json['error_code'] == None
    assert json['status']['code'] == 200
    assert json['status']['messsage'] == 'OK'
    return json

def get_rapidspike_data_for_account(public_key, private_key):
    """
    Input credentials, returns Ping, TCP and HTTP data from RapidSpike
    """
    # Configuration options for each monitor type to avoid running an
    # almost identical for loop for each one.
    # To be accessed with a default fall back so that only configuration
    # options that differ from the default need to be supplied.
    monitor_types = {   'ping': {   },
                        'tcp':  {   'type': 'label'},
                        'http': {   'additional_path_to_data': 'http_monitors',
                                    'name': 'website_domain'}}
    # Mapping RapidSpike statuses to the ones used by the Warboard, as
    # initially set by Pingdom
    status_mapping = {  'passing': 'up',
                        'failing': 'down',
                        'pending': 'paused'}
    checks = []
    for monitor in monitor_types:
        # I'm not sure if I love passing things through in the url and
        # in the params rather than all in the params but it all ends up
        # at the same place
        api_response = rapidspike_api_call('/v1/{}monitors?stats=status, latest_response'.format(monitor), public_key, private_key)
        if 'additional_path_to_data' in monitor_types[monitor]:
            data = api_response['data'][monitor_types[monitor]['additional_path_to_data']]
        else:
            data = api_response['data']

        for check in data:
            # Currently erroring on no website domain
            check_data = {}
            # Check the status, use blue (paused) for all unknown statuses
            check_data['status'] = 'paused'
            # Use custom name field falling back to asset_title
            check_data['name'] = check['monitor'][monitor_types[monitor].get('name', 'asset_title')]
            # Use custom type field falling back to type
            check_data['type'] = check['monitor'][monitor_types[monitor].get('type', 'type')]
            # Get the last response
            check_data['lastresponsetime'] = int(check['stats']['latest_response'])
            # If the monitor is paused then we can skip the rest of this
            # section
            if not check['monitor']['paused']:
                # We need to log unrecognised statuses so they can be
                # categorised correctly rather than all being blue
                if check['stats']['status'] in status_mapping:
                    check_data['status'] = status_mapping[check['stats']['status']]
                else:
                    logger.warning("RapidSpike returned an unknown unknown status '{}' for '{}'".format(check['stats']['status'], check_data['name']))

            checks.append(check_data)

    return checks

def get_rapidspike_data():
    """
    Get RapidSpike data for all accounts in rapidspike_credentials
    """
    rapidspike_data = []
    rapidspike_validity = {}
    rapidspike_validity['failed_accounts'] = 0
    rapidspike_validity['total_accounts'] = 0
    rapidspike_validity['up'] = 0
    rapidspike_validity['down'] = 0
    rapidspike_validity['paused'] = 0
    for account in rapidspike_credentials:
        rapidspike_validity['total_accounts'] += 1
        try:
            data = get_rapidspike_data_for_account(rapidspike_credentials[account]['public_key'], rapidspike_credentials[account]['private_key'])
        except Exception as e:
            logger.error("Could not get data for RapidSpike account '{}'".format(account))
            #logger.exception(e)

            rapidspike_validity['failed_accounts'] += 1
            continue

        for check in data:
            rapidspike_data.append(check)
            rapidspike_validity[check['status']] += 1

    # Data should be considerd stale after 5 minutes
    rapidspike_validity['valid_until'] = time.time() * 1000 + 300000
    return rapidspike_data, rapidspike_validity

if __name__ == '__main__':
    import pprint
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.WARN)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(get_rapidspike_data_for_account(rapidspike_credentials['testuser']['public_key'], rapidspike_credentials['testuser']['private_key']))
