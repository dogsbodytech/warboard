import requests
import time
from modules.config import datadog_orgs

# TODO:
# Add specific error handling for common errors, when errors are caught,
# increment the value of failed_accounts

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
        datadog_data[org] = {}
        datadog_data_validity['total_accounts'] += 1
        datadog_url = datadog_orgs[org]['datadog_url']
        datadog_api_key = datadog_orgs[org]['datadog_api_key']
        datadog_app_key = datadog_orgs[org]['datadog_app_key']
        datadog_timeout = datadog_orgs[org].get('datadog_timeout', 15)
        headers = { 'DD-API-KEY': datadog_api_key,
                    'DD-APPLICATION-KEY': datadog_app_key}
        now = int(time.time())
        five_mins_ago = now - 300
        # Query metric information required for warboard summary
        for query_name, query in summary_queries.items():
            params = {'from': five_mins_ago, 'to': now, 'query': query}
            r = requests.get(   '{}/v1/query'.format(datadog_url),
                                params=params,
                                headers=headers,
                                timeout=datadog_timeout)
            r.raise_for_status()
            for host in r.json()['series']:
                datadog_data_validity['total_checks'] += 1
                hostname = host['scope']
                # Pull the latest value out of the pointlist which is a list
                # containing lists in the form timestamp, value
                metric_value = host['pointlist'][-1][1]
                # Hostnames are assumed to be globally unique even across orgs
                if hostname not in datadog_data[org]:
                    datadog_data[org][hostname] = {}
                    datadog_data[org][hostname]['summary'] = {}
                    datadog_data[org][hostname]['health_status'] = 'blue'

                datadog_data[org][hostname]['name'] = hostname
                datadog_data[org][hostname]['summary'][query_name] = metric_value

        for hostname in datadog_data[org]:
            datadog_data[org][hostname]['orderby'] = max(
                datadog_data[org][hostname]['summary']['cpu'],
                datadog_data[org][hostname]['summary']['memory'],
                datadog_data[org][hostname]['summary']['fullest_disk'],
                datadog_data[org][hostname]['summary']['disk_io'])

        # Query alerting status and use it to set health status
        params = {'group_states': 'all'}
        r = requests.get(   '{}/v1/monitor'.format(datadog_url),
                            params=params,
                            headers=headers,
                            timeout=datadog_timeout)
        r.raise_for_status()
        hosts_with_an_alerting_status = {}
        for monitor in r.json():
            for hostname, state in monitor['state']['groups'].items():
                if hostname not in hosts_with_an_alerting_status:
                    hosts_with_an_alerting_status[hostname] = []

                hosts_with_an_alerting_status[hostname].append(state['status'])

        for hostname, states in hosts_with_an_alerting_status.items():
            if 'No Data' in states:
                status = 'blue'
            elif 'Alert' in states:
                status = 'red'
            elif 'Warn' in states:
                status = 'orange'
            elif 'OK' in states:
                status = 'green'
            if hostname not in datadog_data[org]:
                if status == 'green':
                    pass
                else:
                    datadog_data[org][hostname] = {}
                    datadog_data[org][hostname]['summary'] = {}
                    datadog_data[org][hostname]['name'] = hostname
                    datadog_data[org][hostname]['orderby'] = 0
            datadog_data[org][hostname]['health_status'] = status

    # Data will be valid for 5 minutes after the module runs
    datadog_data_validity['valid_until'] = time.time() * 1000 + 300000
    return datadog_data, datadog_data_validity
