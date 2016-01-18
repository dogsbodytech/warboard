import requests, base64
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
                    pingdom_data[account] = r.json()['checks']
            except requests.exceptions.RequestException:
                pingdom_data[account] = None
    return(pingdom_data)
