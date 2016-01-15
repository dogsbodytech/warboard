import requests, math
from config import sirportly_key, sirportly_token, sirportly_users, sirportly_endpoint, sirportly_red_filter
from config import sirportly_total_filter, sirportly_reduser_filter, sirportly_greenuser_filter, sirportly_unassigned_filter

def sirportly_filter(filterid, user):
    if user != False:
        endpoint = sirportly_endpoint+'/filter?filter='+filterid+'&user='+user
    else:
        endpoint = sirportly_endpoint+'/filter?filter='+filterid
    try:
        r = requests.get(endpoint, headers={'X-Auth-Token': sirportly_token, 'X-Auth-Secret': sirportly_key})
        if r.status_code != requests.codes.ok:
            raise requests.exceptions.RequestException
        return(r.json()['pagination']['total_records'])
    except requests.exceptions.RequestException:
        return(0)

def get_sirportly_data():
    sirportly_data = {'users': {}}
    sirportly_data['unassigned_tickets'] = sirportly_filter(sirportly_unassigned_filter, False)
    sirportly_data['total_tickets'] = sirportly_filter(sirportly_total_filter, False)
    sirportly_data['red_tickets'] = sirportly_filter(sirportly_red_filter, False)
    for user in sirportly_users:
        sirportly_data['users'][user+'_red'] = sirportly_filter(sirportly_reduser_filter, user)
        sirportly_data['users'][user+'_green'] = sirportly_filter(sirportly_greenuser_filter, user)
        sirportly_data['users'][user+'_total'] = sirportly_data['users'][user+'_green']+sirportly_data['users'][user+'_red']
    sirportly_data['multiplier'] = sirportly_ticket_multiplier(sirportly_data['unassigned_tickets'], sirportly_data['users'])
    try:
        sirportly_data['red_percent'] = math.ceil(100*float(sirportly_data['red_tickets'])/float(sirportly_data['total_tickets']))
    except ZeroDivisionError:
        sirportly_data['red_percent'] = 0
    sirportly_data['green_percent'] = 100-sirportly_data['red_percent']
    return(sirportly_data)

def sirportly_ticket_multiplier(unassigned, user_data):
    ticket_counts = [unassigned]
    for user in sirportly_users:
        ticket_counts.append(user_data[user+'_total'])
    try:
        multiplier = math.trunc(100/max(ticket_counts))
    except ZeroDivisionError:
        multiplier = 0
    if multiplier < 1:
        return(1)
    else:
        return(multiplier)
