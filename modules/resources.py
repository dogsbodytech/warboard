from __future__ import division
import json
import time
from redis_functions import get_data, set_volatile_data, get_all_data, set_data, delete_data
from misc import log_messages, to_uuid

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

    # Defaults for when no data is reported, working towards having modules be
    # modular / optional
    resource_results['blue_percent'] = 100
    resource_results['red_percent'] = 0
    resource_results['orange_percent'] = 0
    resource_results['green_percent'] = 0
    resource_results['working_percentage'] = 100

    # Check how many accounts failed from each module and add them to the
    # total failed accounts.  If the data from a module is considered stale
    # then all of it's accounts will be considered failed.
    milliseconds_since_epoch = time.time() * 1000
    for module in get_all_data('resources_success:*'):
        module_success_json = get_data(module)
        module_success = json.loads(module_success_json)[0]
        resource_results['total_accounts'] += module_success['total_accounts']
        resource_results['total_checks'] += module_success['total_checks']
        milliseconds_since_epoch_module_data_is_valid_until = module_success['valid_until']
        if milliseconds_since_epoch > milliseconds_since_epoch_module_data_is_valid_until:
            resource_results['failed_accounts'] += module_success['total_accounts']
            log_messages('Data for {} is stale, please check the daemon is functioning properly'.format(module), 'warning')
        else:
            resource_results['failed_accounts'] += module_success['failed_accounts']

    # We will count checks in so we can compare it against the number of checks
    # reported by the daemon
    checks_found = 0
    # Get list of keys in the format resources:module#uuid
    for host in get_all_data('resources:*'):
        try:
            # Storing lists with only one value since when I convert
            # dictionaries to json and store them in redis they come back as
            # strings, I am working around this by storing lists,
            # ast.literal_eval also works
            host_data = json.loads(get_data(host))[0]
            resource_results['checks'].append(host_data)
            # get the health status colour of the current check, and then add
            # one to the number of checks with that health status
            resource_results[host_data['health_status']] += 1
            checks_found += 1
        except Exception as e:
            # I would rather log to uwsgi's log but I'll sort this out later
            log_messages('Data for {} is not in a valid format: {}'.format(host, e), 'error')

    # If we are getting back old checks that are no-longer reporting hence
    # are not in the total_checks variable then they have failed.
    # If we are getting back less checks than we stored then something has
    # gone really wrong or we caught the weekly cron that clears the keys.
    if resource_results['total_checks'] != checks_found:
        log_messages('The number of checks stored in the database doesn\'t '\
            'match the number reported by the daemon, it is likely some '\
            'servers are no-longer reporting, run '\
            'modules/resources_list_unreporting_servers.py to debug this.',
            'warning')

    # The number of checks we are outputing is authoritive over the number
    # we expected to be there, at the moment we are just logging the fact they
    # were different, it would be nice to have a visual display or send an
    # email but there isn't a correct place to do this at the moment
    resource_results['total_checks'] = checks_found

    total_results = resource_results['green'] + resource_results['red'] + resource_results['orange'] + resource_results['blue']
    if total_results != 0:
        resource_results['red_percent'] = ( resource_results['red'] / total_results ) * 100
        resource_results['orange_percent'] = ( resource_results['orange'] / total_results ) * 100
        resource_results['blue_percent'] = ( resource_results['blue'] / total_results ) * 100
        # I want the percentage to always be 100 and green seems the most
        # disposable / least affected by any rounding issues
        resource_results['green_percent'] = 100 - ( resource_results['red_percent'] + resource_results['orange_percent'] + resource_results['blue_percent'] )

    resource_results['working_percentage'] = 100 - (( resource_results['failed_accounts'] / resource_results['total_accounts'] ) * 100 )
    resource_results['working_accounts'] = resource_results['total_accounts'] - resource_results['failed_accounts']
    return resource_results

def store_resource_data(module_name, data, validity):
    """
    Store data returned by get_module_name_data in redis as key value pairs
    The module must return data in the format returned by get_prometheus_data
    other modules will be moved over to this format since it doesn't allow
    host names to collide between accounts
    """
    for account in data:
        for host in data[account]:
            uuid = to_uuid('{}{}'.format(account, host))
            if data[account][host].get('volatile') == True:
                set_volatile_data('resources:{}#{}'.format(module_name, uuid), json.dumps([data[account][host]]), 300)
            else:
                set_data('resources:{}#{}'.format(module_name, uuid), json.dumps([data[account][host]]))

    set_data('resources_success:{}'.format(module_name), json.dumps([validity]))

def clear_resources_keys():
    for key in get_all_data('resources:*'):
        delete_data(key)
