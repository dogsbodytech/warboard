from misc import log_errors, refresh_time
from time import sleep
from calendar_functions import store_calendar_items
from pingdom import store_pingdom_results
from newrelic import store_newrelic_results
from sirportly import store_sirportly_results

def store_results():
    store_pingdom_results()
    store_newrelic_results()
    store_sirportly_results()
    store_calendar_items()

if __name__ == '__main__':
    log_errors('Warboard backend daemon started!')
    while True:
        try:
            store_results()
        except Exception as e:
            log_errors('Warboard backend daemon failed!')
        sleep(refresh_time())
