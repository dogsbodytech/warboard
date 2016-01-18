import redis
from misc import log_errors
from redis_con import redis_connect
from pingdom import get_pingdom_results, store_pingdom_results
from newrelic import get_newrelic_results, store_newrelic_results
from sirportly import get_sirportly_results, store_sirportly_results

rcon = redis_connect()

def get_results():
    pingdom_results = get_pingdom_results()
    return(pingdom_results)

def store_results():
    store_pingdom_results()
    store_newrelic_results()
    store_sirportly_results()

def set_data(key, value):
    try:
        rcon.set(key, value)
    except redis.exceptions.ConnectionError:
        log_errors('Could not set '+key+' in Redis')

def get_data(key):
    try:
        value = rcon.get(key)
    except redis.exceptions.ConnectionError:
        log_errors('Could not get '+key+' from Redis')
        return(None)
    return(value)

if __name__ == '__main__':
    store_results()
    print(get_results)
