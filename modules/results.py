import redis
from misc import log_errors
from calendar_functions import store_calendar_items, get_calendar_items
from pingdom import get_pingdom_results, store_pingdom_results
from newrelic import get_newrelic_results, store_newrelic_results
from sirportly import get_sirportly_results, store_sirportly_results

def get_results():
    return(store_calendar_items())

def store_results():
    store_pingdom_results()
    store_newrelic_results()
    store_sirportly_results()
    store_calendar_items()

if __name__ == '__main__':
    #store_results()
    print(get_results())
