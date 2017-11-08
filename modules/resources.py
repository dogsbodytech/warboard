from __future__ import division
import json
import time
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
    resource_results['checks'] = []
    resource_results['green'] = 0
    resource_results['red'] = 0
    resource_results['orange'] = 0
    resource_results['blue'] = 0
    resource_results['failed_accounts'] = 0
    resource_results['total_accounts'] = 0
    resource_results['total_checks'] = 0
    resource_results['successful_checks'] = 0

    # Defaults for when no data is reported, working towards having modules be
    # modular / optional
    resource_results['blue_percent'] = 100
    resource_results['red_percent'] = 0
    resource_results['orange_percent'] = 0
    resource_results['green_percent'] = 0
    resource_results['working_percentage'] = 100

    # Check if the data recieved from each module is still valid, if it is not
    # then all checks from that module are counted as unsuccessful and all
    # accounts are counted as failed
    milliseconds_since_epoch = time.time() * 1000
    for module in get_all_data('resources_success:*'):
        module_success_json = get_data(module)
        module_success = json.loads(module_success_json)[0]
        resource_results['total_accounts'] += module_success['total_accounts']
        resource_results['total_checks'] += module_success['total_checks']
        milliseconds_since_epoch_module_data_is_valid_until = module_success['valid_until']
        if milliseconds_since_epoch > milliseconds_since_epoch_module_data_is_valid_until:
            resource_results['failed_accounts'] += module_success['total_accounts']
        else:
            resource_results['failed_accounts'] += module_success['failed_accounts']
            resource_results['successful_checks'] += module_success['successful_checks']

    # Get list of keys using new host system resources:module#uuid
    for host in get_all_data('resources:*'):
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
    if total_results != 0:
        resource_results['red_percent'] = ( resource_results['red'] / total_results ) * 100
        resource_results['orange_percent'] = ( resource_results['orange'] / total_results ) * 100
        resource_results['blue_percent'] = ( resource_results['blue'] / total_results ) * 100
        # I want the percentage to always be 100 and green seems the most
        # disposable / least affected by any rounding issues
        resource_results['green_percent'] = 100 - ( resource_results['red_percent'] + resource_results['orange_percent'] + resource_results['blue_percent'] )

    # Set the working percentage to the lowest of accounts and checks, if either
    # have a total of 0 then resources isn't working so the working percentage
    # can be set to 0 to avoid dividing by 0
    if resource_results['total_accounts'] != 0:
        accounts_working_percentage = 100 - (( resource_results['failed_accounts'] / resource_results['total_accounts'] ) * 100 )
        if accounts_working_percentage < resource_results['working_percentage']:
            resource_results['working_percentage'] = accounts_working_percentage

    else:
        resource_results['working_percentage'] = 0

    if resource_results['total_checks'] != 0:
        checks_working_percentage = ( resource_results['successful_checks'] / resource_results['total_checks'] ) * 100
        if checks_working_percentage < resource_results['working_percentage']:
            resource_results['working_percentage'] = checks_working_percentage

    else:
        resource_results['working_percentage'] = 0

    return resource_results
