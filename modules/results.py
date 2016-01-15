from redis_con import redis_connect
from pingdom import get_pingdom_data
from newrelic import get_newrelic_data
from sirportly import get_sirportly_data

rcon = redis_connect()

def store_results():
    sirportly_data = get_sirportly_data()
    #pingdom_data = get_pingdom_data()
    #newrelic_data = get_newrelic_data()
    for key in sirportly_data:
        if key == 'users':
            for key in sirportly_data['users']:
                try:
                    rcon.set(key, sirportly_data['users'][key])
                except redis.exceptions.ConnectionError:
                    print('Could not connect to Redis!')
        else:
            try:
                rcon.set(key, sirportly_data['users'][key])
            except redis.exceptions.ConnectionError:
                print('Could not connect to Redis!')

if __name__ == '__main__':
    store_results()
