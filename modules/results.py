import redis # needed for exception catching
from redis_con import redis_connect
from pingdom import get_pingdom_data
from newrelic import get_newrelic_data
from sirportly import get_sirportly_data
from misc import log_errors

rcon = redis_connect()

def store_sirportly_results():
    sirportly_data = get_sirportly_data()
    for key in sirportly_data:
        if key == 'users':
            for key in sirportly_data['users']:
                set_data(key, sirportly_data['users'][key])
        else:
            set_data(key, sirportly_data[key])

def store_pingdom_results():
    failed_pingdom = 0
    total_accounts = 0
    pingdom_data = get_pingdom_data()
    for account in pingdom_data:
        if pingdom_data[account] != None:
            set_data('pingdom_'+account, pingdom_data[account])
        else:
            failed_pingdom +=1
            log_errors('Could not get pingdom data for '+account)
        total_accounts +=1
    set_data('total_pingdom_accounts', total_accounts)
    set_data('failed_pingdom', failed_pingdom)

def store_newrelic_results():
    newrelic_data = get_newrelic_data()

def set_data(key, value):
    try:
        rcon.set(key, value)
    except redis.exceptions.ConnectionError:
        log_errors('Could not write '+key+' to Redis.')

if __name__ == '__main__':
    store_pingdom_results()
