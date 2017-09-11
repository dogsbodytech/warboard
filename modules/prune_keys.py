from config import pingdom_keys, newrelic_servers_keys
from redis_functions import get_all_data, delete_data

def prune_old_keys():
    for key in get_all_data('pingdom_*'):
        if key.split('pingdom_')[1] not in pingdom_keys:
            delete_data(key)
    for key in get_all_data('resources_newrelic_servers_*'):
        if key.split('resources_newrelic_servers_')[1] not in newrelic_keys:
            delete_data(key)
