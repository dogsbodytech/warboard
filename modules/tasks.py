import sys, getpass
from config import warboard_user
from misc import log_messages
from calendar_functions import store_calendar_items
from prune_keys import prune_old_keys

def hourly_tasks():
    store_calendar_items()
    prune_old_keys()

def daily_tasks():
    return(False)

def weekly_tasks():
    return(False)

if __name__ == '__main__':
    if getpass.getuser() != warboard_user:
        print('Please run the warboard with the correct user: '+warboard_user)
        exit(1)
    if len(sys.argv) == 2:
        if 'hourly' == sys.argv[1]:
            hourly_tasks()
            log_messages('Hourly tasks executed', 'info')
        elif 'daily' == sys.argv[1]:
            daily_tasks()
            log_messages('Daily tasks executed', 'info')
        elif 'weekly' == sys.argv[1]:
            weekly_tasks()
            log_messages('Weekly tasks executed', 'info')
        else:
            print('Invalid option!')
            exit(2)
    else:
        print('Valid tasks: hourly|daily|weekly')
        exit(2)
