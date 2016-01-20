import itertools, datetime, json
from time import strftime
from config import warboard_log

def log_errors(error):
    lf = open(warboard_log, 'ab')
    current_time = strftime("%d-%m-%Y %H:%M:%S: ")
    lf.write(current_time+error)
    lf.close()

def chain_results(results):
    return(list(itertools.chain(*results)))

def refresh_time():
    now = datetime.datetime.now()
    if now.isoweekday() in range(6, 7):
        return(60)
    elif datetime.time(hour=7) <= now.time() <= datetime.time(hour=18):
        return(15)
    else:
        return(60)
