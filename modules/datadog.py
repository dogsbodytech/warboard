import requests
import time
from modules.redis_functions import set_data, get_data
from modules.config import datadog_url, datadog_orgs
from modules.misc import to_uuid

# TODO:
# v1/monitor needs to be used for monitor status in order to set status
# add specific error handling for common errors
# set timeouts for requests to the api

def get_datadog_data():
    summary_queries = {
        'cpu':          '100 - avg:system.cpu.idle{*} by {host}',
        'memory':       '100 - ( ( 100 / avg:system.mem.total{*} by {host} )'\
                        ' * avg:system.mem.usable{*} by {host} )',
        'disk_io':      'avg:system.io.util{*} by {host}',
        'fullest_disk': '( 100 / avg:system.disk.total{*} by {host} )'\
                        ' * avg:system.disk.used{*} by {host}'
    }
    datadog_data = {}
    datadog_data_validity = {}
    datadog_data_validity['failed_accounts'] = 0
    datadog_data_validity['total_accounts'] = 0
    datadog_data_validity['total_checks'] = 0
    for org in datadog_orgs:
        datadog_data_validity['total_accounts'] += 1
        datadog_api_key = datadog_orgs[org]['datadog_api_key']
        datadog_app_key = datadog_orgs[org]['datadog_app_key']
        headers = { 'DD-API-KEY': datadog_api_key,
                    'DD-APPLICATION-KEY': datadog_app_key}
        now = int(time.time())
        five_mins_ago = now - 300
        #r = requests.get('{}v1/validate'.format(datadog_url), headers=headers)
        for query_name, query in summary_queries.items():
            params={'from': five_mins_ago, 'to': now, 'query': query}
            r = requests.get(   '{}v1/query'.format(datadog_url),
                                params=params,
                                headers=headers)
            r.raise_for_status()
            for host in r.json()['series']:
                datadog_data_validity['total_checks'] += 1
                hostname = host['scope'].replace('host:', '')
                # Pull the latest value out of the pointlist which is a list
                # containing lists in the form timestamp, value
                metric_value = host['pointlist'][-1][1]
                # Hostnames are assumed to be globally unique even across orgs
                if hostname not in datadog_data:
                    datadog_data[hostname] = {}
                    datadog_data[hostname]['summary'] = {}
                    datadog_data[hostname]['health_status'] = 'blue'

                datadog_data[hostname]['name'] = hostname
                datadog_data[hostname]['summary'][query_name] = metric_value

        for hostname in datadog_data:
            datadog_data[hostname]['orderby'] = max(
                datadog_data[hostname]['summary']['cpu'],
                datadog_data[hostname]['summary']['memory'],
                datadog_data[hostname]['summary']['fullest_disk'],
                datadog_data[hostname]['summary']['disk_io'])

    # Data will be valid for 5 minutes after the module runs
    datadog_data_validity['valid_until'] = time.time() * 1000 + 300000
    return datadog_data, datadog_data_validity

def store_datadog_data(datadog_data, datadog_data_validity):
    """
    Store data returned by get_datadog_data in redis as key value pairs
    """
    for host in datadog_data:
        host_data = datadog_data[host]
        set_data('resources:datadog#{}'.format(to_uuid(host)),
            json.dumps([host_data]))

    set_data('resources_success:datadog', json.dumps([datadog_data_validity]))
