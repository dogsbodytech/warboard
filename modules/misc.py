import itertools
import datetime
import json
import uuid

def chain_results(results):
    return(list(itertools.chain(*results))) # This chains all results together into one tuple

def refresh_time():
    now = datetime.datetime.now()
    if now.isoweekday() in range(6, 7):
        return(120)
    elif datetime.time(hour=7) <= now.time() <= datetime.time(hour=18): # If its a working hour return a 15 second refresh rate
        return(60)
    else:
        return(120)

def to_uuid(string):
    """
    Mirroring the jinja filter implemented in ansible

    Input a string. Returns the uuid ansible would generate as a string.
    """
    return str(uuid.uuid5(uuid.UUID('361E6D51-FAEC-444A-9079-341386DA8E2E'), string))
