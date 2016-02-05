from misc import log_messages, refresh_time
from time import sleep
from calendar_functions import store_calendar_items, prune_calendar_items
from pingdom import store_pingdom_results
from newrelic import store_newrelic_results
from sirportly import store_sirportly_results

def store_results():
    store_pingdom_results()
    store_newrelic_results()
    store_sirportly_results()
    store_calendar_items() # This should be run hourly, will take a look at this

if __name__ == '__main__':
    log_messages('Warboard backend daemon started!', 'info')
    while True:
        store_results()
        sleep(refresh_time())
