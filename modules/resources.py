from __future__ import division
import json
from newrelic_servers import get_newrelic_servers_results
from newrelic_infrastructure import get_newrelic_infra_results
from redis_functions import get_data, get_all_data
from misc import chain_results, log_messages
from config import newrelic_servers_keys, newrelic_main_and_insights_keys

def get_resource_results():
    """
    Merges lists returned by resource modules into one list in the correct
    format for warboard.html to display monitored resources

    {% for check in resource_results['checks']|sort(attribute='orderby')|reverse %}

    <tr class="danger lead"><td>{{ check['name'] }}</td><td>{{ check['summary']['cpu'] }}%</td><td>{{ check['summary']['memory'] }}%</td><td>{{ check['summary']['disk_io'] }}%</td><td>{{ check['summary']['fullest_disk'] }}%</td></tr>

    """
    resource_results = {}
    resource_results['green'] = 0
    resource_results['red'] = 0
    resource_results['orange'] = 0
    resource_results['blue'] = 0
    resource_results['failed_accounts'] = 0
    resource_results['working_accounts'] = 0
    resource_results['total_accounts'] = 0
    resource_results['checks'] = []
    resource_results['total_checks'] = 0
    resource_results['failed_checks'] = 0

    if newrelic_servers_keys:
        newrelic_servers_results = get_newrelic_servers_results()
        resource_results['green'] += newrelic_servers_results['green']
        resource_results['red'] += newrelic_servers_results['red']
        resource_results['orange'] += newrelic_servers_results['orange']
        resource_results['blue'] += newrelic_servers_results['blue']
        resource_results['checks'] += newrelic_servers_results['checks']
        resource_results['failed_accounts'] += newrelic_servers_results['failed_newrelic_servers_accounts']
        resource_results['total_accounts'] += newrelic_servers_results['total_newrelic_servers_accounts']
        resource_results['total_checks'] += newrelic_servers_results['total_checks']
        resource_results['working_accounts'] += newrelic_servers_results['total_newrelic_servers_accounts'] - newrelic_servers_results['failed_newrelic_servers_accounts']

    if newrelic_main_and_insights_keys:
        newrelic_infra_results = get_newrelic_infra_results()
        resource_results['green'] += newrelic_infra_results['green']
        resource_results['red'] += newrelic_infra_results['red']
        resource_results['orange'] += newrelic_infra_results['orange']
        resource_results['blue'] += newrelic_infra_results['blue']
        resource_results['checks'] += newrelic_infra_results['checks']
        resource_results['failed_accounts'] += newrelic_infra_results['failed_newrelic_infra_accounts']
        resource_results['total_accounts'] += newrelic_infra_results['total_newrelic_infra_accounts']
        resource_results['total_checks'] += newrelic_infra_results['total_checks']
        resource_results['working_accounts'] += newrelic_infra_results['total_newrelic_infra_accounts'] - newrelic_infra_results['failed_newrelic_infra_accounts']

    # Get list of keys using new host system resources_host_uuid
    for host in get_all_data('resources_host_*'):
        resource_results['total_checks'] += 1
        try:
            # Storing lists with only one value since when I convert dictionarys
            # to json and store them in redis they come back as strings, I am
            # working around this by storing lists, ast.literal_eval also works
            host_data = json.loads(get_data(host))[0]
            resource_results['checks'].append(host_data)
            # get the health status colour of the current check, and then add
            # one to the number of checks with that health status
            resource_results[host_data['health_status']] += 1
        except Exception as e:
            resource_results['failed_checks'] += 1
            # I would rather log to uwsgi's log but I'll sort this out later
            log_messages(e, 'error')


    total_results = resource_results['green'] + resource_results['red'] + resource_results['orange'] + resource_results['blue']
    resource_results['red_percent'] = ( resource_results['red'] / total_results ) * 100
    resource_results['orange_percent'] = ( resource_results['orange'] / total_results ) * 100
    resource_results['blue_percent'] = ( resource_results['blue'] / total_results ) * 100
    # I want the percentage to always be 100 and green seems the most disposable and least affected by any rounding issues
    resource_results['green_percent'] = 100 - ( resource_results['red_percent'] + resource_results['orange_percent'] + resource_results['blue_percent'] )

    resource_results['working_percentage'] = 100 - (( resource_results['failed_accounts'] / resource_results['total_accounts'] ) * 100 )

    return resource_results
