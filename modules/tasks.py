import sys, getpass
from config import warboard_user
from calendar_functions import store_calendar_items
from resources import clear_resources_keys
from resources_list_unreporting_servers import list_unreporting_servers
import logging
import logging.handlers
import logging.config

def hourly_tasks():
    store_calendar_items()

def daily_tasks():
    return


def weekly_tasks():
    return

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,  # this fixes the problem
        'formatters': {
            'standard': {
                'format': '%(asctime)s: warboard_tasks.%(name)s: %(levelname)s: %(message)s',
                'datefmt': '%d-%m-%Y %H:%M:%S'
            },
        },
        'handlers': {
            'file': {
                'level':'INFO',
                'class':'logging.handlers.WatchedFileHandler',
                'filename': warboard_log,
                'formatter': 'standard',
            },
        },
        'loggers': {
            '': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True
            },
            'requests.packages.urllib3': {
                'handlers': ['file'],
                'level': 'WARNING'
            }
        }
    })
    if getpass.getuser() != warboard_user:
        print('Please run the warboard with the correct user: '+warboard_user)
        exit(1)
    if len(sys.argv) == 2:
        if 'hourly' == sys.argv[1]:
            hourly_tasks()
            logger.info('Hourly tasks executed')
        elif 'daily' == sys.argv[1]:
            daily_tasks()
            logger.info('Daily tasks executed')
        elif 'weekly' == sys.argv[1]:
            weekly_tasks()
            logger.info('Weekly tasks executed')
        else:
            print('Invalid option!')
            exit(2)
    else:
        print('Valid tasks: hourly|daily|weekly')
        exit(2)
