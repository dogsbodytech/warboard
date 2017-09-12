import itertools, datetime, json, logging
from config import warboard_log

def log_messages(message, priority):
    logging.basicConfig(filename=warboard_log, level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    if priority == 'error':
        logging.error(message)
    elif priority == 'info':
        logging.info(message)
    elif priority == 'warning':
        logging.warning(message)

def chain_results(results):
    return(list(itertools.chain(*results))) # This chains all results together into one tuple

def refresh_time():
    now = datetime.datetime.now()
    if now.isoweekday() in range(6, 7):
        return(60)
    elif datetime.time(hour=7) <= now.time() <= datetime.time(hour=18): # If its a working hour return a 15 second refresh rate
        return(15)
    else:
        return(60)
