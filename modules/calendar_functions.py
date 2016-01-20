import datetime, json
from time import strftime
from config import calendar_export
from redis_functions import set_data, get_data

def get_calendar_items():
    with open(calendar_export) as c_file:
        c_data = json.load(c_file)
    c_file.close()
    for item in c_data['items']:
        old_date = item['start']['date']
        convert = datetime.datetime.strptime(old_date, '%Y-%m-%d')
        item['start']['date'] = convert.strftime('%a %d %B')
    return(c_data['items'])

def store_calendar_items():
    with open(calendar_export) as c_file:
        c_data = json.load(c_file)
    c_file.close()
    for item in c_data['items']:
        current = get_data('calendar_'+item['start']['date'])
        print(current)
