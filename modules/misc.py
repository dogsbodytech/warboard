import itertools, datetime, json
from time import strftime
from config import warboard_log, calendar_export

def log_errors(error):
    lf = open(warboard_log, 'wb')
    current_time = strftime("%d-%m-%Y %H:%M:%S: ")
    lf.write(current_time+error)
    lf.close()

def chain_results(results):
    return(list(itertools.chain(*results)))

def parse_calendar():
    with open(calendar_export) as c_file:
        c_data = json.load(c_file)
    c_file.close()
    for item in c_data['items']:
        old_date = item['start']['date']
        convert = datetime.datetime.strptime(old_date, '%Y-%m-%d')
        item['start']['date'] = convert.strftime('%a %d %B')
    return(c_data['items'])

def refresh_time():
    now = datetime.datetime.now()
    if now.isoweekday() in range(6, 7):
        return(60)
    elif datetime.time(hour=7) <= now.time() <= datetime.time(hour=18):
        return(15)
    else:
        return(60)
