from modules.config import pingdom_keys
from modules.redis_functions import get_all_data, delete_data

def prune_old_keys():
    for key in get_all_data('pingdom_*'):
        if key.split('pingdom_')[1] not in pingdom_keys:
            delete_data(key)
