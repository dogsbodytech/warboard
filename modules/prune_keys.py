from config import pingdom_keys, newrelic_keys
from redis_functions import get_all_data, delete_data

def prune_old_keys():
    for key in get_all_data('pingdom_*'):
        if key not in pingdom_keys:
            delete_data(key)
    for key in get_all_data('newrelic_*'):
        if key not in newrelic_keys:
            delete_data(key)
