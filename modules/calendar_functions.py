import datetime, json
from time import strftime
from config import calendar_export
from redis_functions import set_data, get_data, get_all_data, delete_data

calendar_split = '</li><li class="list-group-item list-group-item-info lead">' # This should only be changed when modifying the template

def get_calendar_items():
    calendar_items = []
    calendar_keys = sorted(get_all_data('calendar_*')) # Get all the calendar keys from Redis
    for key in calendar_keys:
        old_date = key.replace('calendar_', '')
        convert = datetime.datetime.strptime(old_date, '%Y-%m-%d') # Convert the date to a nice format for the Warboard
        calendar_items.append({convert.strftime('%a %d %B'): get_data(key)})
    return(calendar_items)

def prune_calendar_items():
    # We are now pruning all calendar items when reloading the calendar file to remove old entries we don't want.
    calendar_keys = get_all_data('calendar_*')
    for key in calendar_keys:
        delete_data(key)

def store_calendar_items():
    with open(calendar_export) as c_file:
        try:
            c_data = json.load(c_file)
        except ValueError:
            c_data = False
    c_file.close()
    if c_data != False:
        prune_calendar_items()
        for item in c_data['items']:
            if 'dateTime' in item['start']: # Check if the datetime is set
                item['start']['date'] = item['start']['dateTime'].split('T')[0] # Split the datetime to get the date and set the data parameter
                current_summary = item['summary']
                try:
                    start_time = datetime.datetime.strptime(item['start']['dateTime'].split('T')[1], '%H:%M:%SZ').strftime('%H:%M') # Convert the start time to a nice date
                    end_time = datetime.datetime.strptime(item['end']['dateTime'].split('T')[1], '%H:%M:%SZ').strftime('%H:%M: ') # Convert the end time to a nice date
                except ValueError:
                    start_time = datetime.datetime.strptime(item['start']['dateTime'].split('T')[1], '%H:%M:%S+01:00').strftime('%H:%M') # To work with DST times
                    end_time = datetime.datetime.strptime(item['end']['dateTime'].split('T')[1], '%H:%M:%S+01:00').strftime('%H:%M: ')
                item['summary'] = start_time+' - '+end_time+current_summary # Add the start and end time to the summary
            current = get_data('calendar_'+item['start']['date']) # Check if an existing key exists for the date in question
            if current == None:
                set_data('calendar_'+item['start']['date'], item['summary']) # If a date doesn't exist create one
            elif item['summary'] not in current: # If a key exists but it's not the current summary it means we have two items for one date
                set_data('calendar_'+item['start']['date'], current+calendar_split+item['summary']) # Append to the existing item
    else:
        logging.error('Could not parse calendar')
