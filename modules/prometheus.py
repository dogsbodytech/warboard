import requests
from requests.auth import HTTPBasicAuth
import json
from redis_functions import set_data, get_data
from misc import log_messages, to_uuid
from config import prometheus_credentials

def get_prometheus_data():
    """
    Collects data for all prometheus users provided in the config file and
    returns it as a tuple, dictionary containing all servers as key server
    name, value server data and dictionary with meta data for checks returned
    """
    prometheus_data = {}
    prometheus_validity = {}
    prometheus_validity['failed_accounts'] = 0
    prometheus_validity['total_accounts'] = 0
    prometheus_validity['total_checks'] = 0

    #queries = {}
    #queries['cpu'] = '(1 - avg(rate(node_cpu{mode="idle"}[1m])) by (instance)) * 100'
    #queries['memory'] =
    #queries['disk_io'] =
    #queries['disk_space'] =

    query = '(1 - avg(rate(node_cpu{mode="idle"}[1m])) by (instance)) * 100'

    for user in prometheus_credentials:
        prometheus_validity['total_accounts'] += 1
        try:
            metrics_response = requests.get(
                '{}/api/v1/query'.format(prometheus_credentials[user]['url']),
                auth=HTTPBasicAuth(prometheus_credentials[user]['username'],
                prometheus_credentials[user]['password']),
                params={'query': query},
                timeout=prometheus_credentials[user]['timeout'])
            metrics_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            prometheus_validity['failed_accounts'] += 1
            log_messages('Could not get prometheus data for {}: Error: {}'.format(user, e), 'error')
            continue

        metrics_response_json =  json.loads(metrics_response.text)
        prometheus_data[user] = metrics_response_json

    return prometheus_data, prometheus_validity
