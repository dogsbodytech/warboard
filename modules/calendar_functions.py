import datetime, json
from time import strftime
from misc import log_errors
from config import calendar_export
from redis_functions import set_data, get_data, get_all_data

calendar_split = '</li><li class="list-group-item list-group-item-info lead">' # This should only be changed when modifying the template

def get_calendar_items():
    calendar_items = {}
    calendar_keys = get_all_data('calendar_*')
    for key in calendar_keys:
        old_date = key.replace('calendar_', '')
        convert = datetime.datetime.strptime(old_date, '%Y-%m-%d')
    calendar_items[convert.strftime('%a %d %B')] = get_data(key)
    return(calendar_items)

def store_calendar_items():
    with open(calendar_export) as c_file:
        c_data = json.load(c_file)
    c_file.close()
    for item in c_data['items']:
        try:
            current = get_data('calendar_'+item['start']['date'])
            if current == None:
                set_data('calendar_'+item['start']['date'], item['summary'])
            else:
                set_data('calendar_'+item['start']['date'], current+calendar_split+item['summary'])
        except Exception as e: # Using this until support for times is added
            log_errors('Could not parse calendar items')
