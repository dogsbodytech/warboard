import requests, base64, math, json
from redis_functions import set_data, get_data
from misc import log_errors, chain_results
from config import pingdom_keys, pingdom_multiaccounts, pingdom_endpoint, pingdom_timeout

def get_pingdom_data():
    pingdom_data = {}
    for account in pingdom_keys:
        for key in pingdom_keys[account]:
            auth = pingdom_keys[account][key]
            if account in pingdom_multiaccounts:
                email = pingdom_multiaccounts[account][key]
                call_headers = {'Account-Email': email, 'App-Key': key, 'Authorization': 'Basic '+base64.b64encode(auth)}
            else:
                call_headers = {'App-Key': key, 'Authorization': 'Basic '+base64.b64encode(auth)}
            try:
                r = requests.get(pingdom_endpoint, headers=call_headers, timeout=pingdom_timeout)
                if r.status_code != requests.codes.ok:
                    raise requests.exceptions.RequestException
                else:
                    pingdom_data[account] = r.text # We need to store this in redis as text and load it as json when we pull it out
            except requests.exceptions.RequestException:
                pingdom_data[account] = None
    return(pingdom_data)

def store_pingdom_results():
    failed_pingdom = 0
    total_accounts = 0
    pingdom_data = get_pingdom_data() # Get all the pingdom data
    for account in pingdom_data:
        if pingdom_data[account] != None: # If we get a don't get a None store it, otherwise log the error
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
        result_json = json.loads(get_data('pingdom_'+account)) # Load all the pingdom keys as json and store them in the all_results list
        all_results.append(result_json['checks'])
    pingdom_results['pingdom_up'] = 0
    pingdom_results['pingdom_down'] = 0
    pingdom_results['pingdom_paused'] = 0
    pingdom_results['total_pingdom_accounts'] = get_data('total_pingdom_accounts')
    pingdom_results['failed_pingdom'] = int(get_data('failed_pingdom'))
    pingdom_results['working_pingdom'] = int(pingdom_results['total_pingdom_accounts'])-int(pingdom_results['failed_pingdom'])
    pingdom_results['checks'] = chain_results(all_results) # Chain all the results together to be returned for the warboard
    pingdom_results['total_checks'] = len(pingdom_results['checks'])
    for check in pingdom_results['checks']: # Categorize all the checks as up/down etc
        if check['status'] == 'up':
            pingdom_results['pingdom_up'] +=1
        elif check['status'] == 'down':
            pingdom_results['pingdom_down'] +=1
        elif check['status'] == 'paused':
            pingdom_results['pingdom_paused'] +=1
    pingdom_results['down_percent'] = math.ceil(100*float(pingdom_results['pingdom_down'])/float(pingdom_results['total_checks']))
    pingdom_results['paused_percent'] = math.ceil(100*float(pingdom_results['pingdom_paused'])/float(pingdom_results['total_checks']))
    pingdom_results['up_percent'] = 100-pingdom_results['down_percent']-pingdom_results['paused_percent']
    return(pingdom_results)
