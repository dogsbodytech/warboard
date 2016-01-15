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

def get_sirportly_results():
    unassigned_tickets = get_data('alexlast_green')
    print(unassigned_tickets)

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
    failed_newrelic = 0
    total_accounts = 0
    newrelic_data = get_newrelic_data()
    for account in newrelic_data:
        if newrelic_data[account] != None:
            set_data('newrelic_'+account, newrelic_data[account])
        else:
            failed_newrelic +=1
            log_errors('Could not get newrelic data for '+account)
        total_accounts+=1
    set_data('total_newrelic_accounts', total_accounts)
    set_data('failed_newrelic', failed_newrelic)

def set_data(key, value):
    try:
        rcon.set(key, value)
    except redis.exceptions.ConnectionError:
        log_errors('Could not set '+key+' in Redis.')

def get_data(key):
    try:
        rcon.get(key)
    except redis.exceptions.ConnectionError:
        log_errors('Could not get '+key+' from Redis.')

if __name__ == '__main__':
    store_sirportly_results()
    get_sirportly_results()
