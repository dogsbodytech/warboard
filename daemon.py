import sys, getpass
from time import sleep
from modules.misc import log_messages, refresh_time
from modules.daemon import Daemon
from modules.config import warboard_pid_path, warboard_user
from modules.pingdom import store_pingdom_results
from modules.newrelic import store_newrelic_results
from modules.sirportly import store_sirportly_results

class WarboardDaemon(Daemon):
    def run(self):
        while True:
            store_pingdom_results()
            store_newrelic_results()
            store_sirportly_results()
            sleep(refresh_time())

if __name__ == '__main__':
    if getpass.getuser() != warboard_user:
        print('Please run the warboard with the correct user: '+warboard_user)
        exit(1)
    daemon = WarboardDaemon(warboard_pid_path)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            log_messages('Warboard backend daemon started!', 'info')
            daemon.start()
        elif 'stop' == sys.argv[1]:
            log_messages('Warboard backend daemon stopped!', 'info')
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print('Invalid option!')
            exit(2)
    else:
        print('usage: start|stop|restart')
        exit(2)
