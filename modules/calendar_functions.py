import datetime, json
from time import strftime
from config import calendar_export
from redis_functions import set_data, get_data, get_all_data

calendar_split = '</li><li class="list-group-item list-group-item-info lead">' # This should only be changed when modifying the template

def get_calendar_items():
    calendar_items = get_all_data('calendar_*')
    #old_date = item['start']['date']
    #convert = datetime.datetime.strptime(old_date, '%Y-%m-%d')
    #item['start']['date'] = convert.strftime('%a %d %B')
    return(calendar_items)

def store_calendar_items():
    with open(calendar_export) as c_file:
        c_data = json.load(c_file)
    c_file.close()
    for item in c_data['items']:
        current = get_data('calendar_'+item['start']['date'])
        if current == None:
            set_data('calendar_'+item['start']['date'], item['summary'])
        else:
            set_data('calendar_'+item['start']['date'], current+calendar_split+item['summary'])
