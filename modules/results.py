from redis import redis_connect
from pingdom import get_pingdom_data
from newrelic import get_newrelic_data
from sirportly import get_sirportly_data

rcon = redis_connect()

def store_results():
    sirportly_data = get_sirportly_data()
    pingdom_data = get_pingdom_data()
    newrelic_data = get_newrelic_data()
    print(sirportly_data)
    print(pingdom_data)
    print(newrelic_data)

if __name__ == '__main__':
    store_results()
