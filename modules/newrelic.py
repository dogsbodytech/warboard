import requests
from config import newrelic_keys, newrelic_timeout, newrelic_endpoint

def get_newrelic_data():
    newrelic_results = {}
    for account in newrelic_keys:
        try:
            r = requests.get(newrelic_endpoint, headers={'X-Api-Key': newrelic_keys[account]}, timeout=newrelic_timeout)
            if r.status_code != requests.codes.ok:
                raise requests.exceptions.RequestException
            else:
                newrelic_results[account] = r.json()['servers']
        except requests.exceptions.RequestException:
            newrelic_results[account] = None
    return(newrelic_results)
