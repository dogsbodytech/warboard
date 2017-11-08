from __future__ import division
import json
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
    # success dictionarys need a timestamp, to check the redis data is up to
    # date, if it isn't then all checks can be considered failed
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


    # The following two sections need a rewrite to:
    # Use an new key naming convention.
    # Include a stored in redis timestamp that will be used to
    # determine if the data is old and hence all accounts should be counted as
    # failed.
    # Decide and implement the way failed checks will be implemented, I am
    # currently thinking the lowest of the working accounts and successful
    # checks percentage should be the percentage displayed.  The user will then
    # need to check the logs which should be written to by the module that
    # reports failed accounts / checks.
    newrelic_servers_accounts_json = get_data('resources_success_newrelic_servers')
    if newrelic_servers_accounts_json:
        newrelic_servers_accounts = json.loads(newrelic_servers_accounts_json)[0]
        resource_results['failed_accounts'] += newrelic_servers_accounts['failed_newrelic_servers_accounts']
        resource_results['total_accounts'] += newrelic_servers_accounts['total_newrelic_servers_accounts']
        resource_results['working_accounts'] += newrelic_servers_accounts['total_newrelic_servers_accounts'] - newrelic_servers_accounts['failed_newrelic_servers_accounts']


    infrastructure_accounts_json = get_data('resources_success_newrelic_infrastructure')
    if infrastructure_accounts_json:
        infrastructure_accounts = json.loads(infrastructure_accounts_json)[0]
        resource_results['failed_accounts'] += infrastructure_accounts['failed_newrelic_infra_accounts']
        resource_results['total_accounts'] += infrastructure_accounts['total_newrelic_infra_accounts']
        resource_results['working_accounts'] += infrastructure_accounts['total_newrelic_infra_accounts'] - infrastructure_accounts['failed_newrelic_infra_accounts']


    # Get list of keys using new host system resources_host_uuid
    for host in get_all_data('resources_host:*'):
        resource_results['total_checks'] += 1
        # This might be a good place to check the timestamp and make the check
        # a failed check if it is more than 5 minutes old, we still need to
        # display the failed checks as a percentage since this is how the failed
        # accounts percentage works, it could be better do decied which checks
        # are too old in the jinja filter and handle displaying them differently
        # right at the end
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
