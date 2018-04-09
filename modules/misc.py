import itertools
import datetime
import json
import logging
import logging.handlers
import uuid
from config import warboard_log, warboard_title

def setup_logging():
    log_handler = logging.handlers.WatchedFileHandler(warboard_log)
    formatter = logging.Formatter('%(asctime)s {}: %(levelname)s: %(message)s'.format(warboard_title.lower().replace(' ', '_')), '%d-%m-%Y %H:%M:%S')
    log_handler.setFormatter(formatter)
    #logger = logging.getLogger(__name__)
    logger = logging.getLogger()
    logger.addHandler(log_handler)
    #logging.getLogger('requests').setLevel(logging.CRITICAL)
    logger.setLevel(logging.DEBUG)

def log_messages(message, priority):
    setup_logging()
    if priority == 'error':
        logging.error(message)
    elif priority == 'info':
        logging.info(message)
    elif priority == 'warning':
        logging.warning(message)
    elif priority == 'debug':
        logging.debug(message)
    else:
        logging.error('Unexpected priority used:{} :'.format(priority, message))


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

def to_uuid(string):
    """
    Mirroring the jinja filter implemented in ansible

    Input a string. Returns the uuid ansible would generate as a string.
    """
    return str(uuid.uuid5(uuid.UUID('361E6D51-FAEC-444A-9079-341386DA8E2E'), string.encode('utf-8')))
