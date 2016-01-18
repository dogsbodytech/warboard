import redis # needed for exception catching
from redis_con import redis_connect
from pingdom import get_pingdom_data
from newrelic import get_newrelic_data
from sirportly import get_sirportly_data
from misc import log_errors, chain_results
from config import sirportly_users, pingdom_keys, newrelic_keys

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
    sirportly_results = {'users': {}}
    sirportly_results['unassigned_tickets'] = get_data('unassigned_tickets')
    sirportly_results['red_percent'] = get_data('red_percent')
    sirportly_results['green_percent'] = get_data('green_percent')
    sirportly_results['multiplier'] = get_data('multiplier')
    sirportly_results['red_tickets'] = get_data('red_tickets')
    sirportly_results['total_tickets'] = get_data('total_tickets')
    for user in sirportly_users:
        sirportly_results['users'][user+'_green'] = get_data(user+'_green')
        sirportly_results['users'][user+'_red'] = get_data(user+'_red')
        sirportly_results['users'][user+'_total'] = get_data(user+'_total')
    return(sirportly_results)

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

def get_pingdom_results():
    all_results = []
    pingdom_results = {}
    for account in pingdom_keys:
        all_results.append(get_data('pingdom_'+account))
    pingdom_results['total_pingdom_accounts'] = get_data('total_pingdom_accounts')
    pingdom_results['failed_pingdom'] = get_data('failed_pingdom')
    pingdom_results['checks'] = chain_results(all_results)
    return(pingdom_results)

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

def get_newrelic_results():
    all_results = []
    newrelic_results = {}
    for account in newrelic_keys:
        all_results.append(get_data('newrelic_'+account))
    newrelic_results['total_newrelic_accounts'] = get_data('total_newrelic_accounts')
    newrelic_results['failed_newrelic'] = get_data('failed_newrelic')
    newrelic_results['checks'] = chain_results(all_results)
    return(newrelic_results)

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
    store_pingdom_results()
    store_newrelic_results()
    store_sirportly_results()
    print(get_newrelic_results())
    print(get_sirportly_data())
