from config import pingdom_keys #, newrelic_servers_keys, newrelic_main_and_insights_keys
from redis_functions import get_all_data, delete_data


# Prune keys needs to be written to include resources as a long term thing but
# for now I will do so by hand.
def prune_old_keys():
    for key in get_all_data('pingdom_*'):
        if key.split('pingdom_')[1] not in pingdom_keys:
            delete_data(key)
