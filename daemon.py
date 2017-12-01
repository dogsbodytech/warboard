import sys, getpass
from time import sleep
from modules.misc import log_messages, refresh_time
from modules.daemon import Daemon
from modules.config import warboard_pid_path, warboard_user
from modules.pingdom import store_pingdom_results
from modules.newrelic_servers import get_newrelic_servers_data, store_newrelic_servers_data
from modules.newrelic_infrastructure import get_newrelic_infra_data, store_newrelic_infra_data
from modules.tick import get_tick_data, store_tick_data
from modules.sirportly import store_sirportly_results
from modules.prune_keys import prune_old_keys

class WarboardDaemon(Daemon):
    def run(self):
        try:
            prune_old_keys()
        except Exception as e:
            log_messages('prune_old_keys failed {}'.format(e), 'error')
        while True:
            try:
                store_pingdom_results()
            except Exception as e:
                log_messages('store_pingdom_results failed {}'.format(e), 'error')
            try:
                store_newrelic_servers_data(*get_newrelic_servers_data())
            except Exception as e:
                log_messages('store_newrelic_servers_data failed {}'.format(e), 'error')
            try:
                store_newrelic_infra_data(*get_newrelic_infra_data())
            except Exception as e:
                log_messages('store_newrelic_infra_data {}'.format(e), 'error')
            try:
                store_tick_data(*get_tick_data())
            except Exception as e:
                log_messages('store_tick_data {}'.format(e), 'error')
            try:
                store_sirportly_results()
            except Exception as e:
                log_messages('store_sirportly_results {}'.format(e), 'error')
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
            log_messages('Warboard backend daemon restarted!', 'info')
            daemon.restart()
        else:
            print('Invalid option!')
            exit(2)
    else:
        print('usage: start|stop|restart')
        exit(2)
