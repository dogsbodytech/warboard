import sys, getpass
import logging
import logging.handlers
from time import sleep
from modules.config import warboard_log, warboard_title
from modules.misc import refresh_time
from modules.daemon import Daemon
from modules.config import warboard_pid_path, warboard_user
from modules.pingdom import store_pingdom_results
from modules.newrelic_servers import get_newrelic_servers_data, store_newrelic_servers_data
from modules.newrelic_infrastructure import get_newrelic_infra_data, store_newrelic_infra_data
from modules.tick import get_tick_data, store_tick_data
from modules.prometheus import get_prometheus_data
from modules.resources import store_resource_data
from modules.sirportly import store_sirportly_results
from modules.prune_keys import prune_old_keys

class WarboardDaemon(Daemon):
    def run(self):
        try:
            prune_old_keys()
        except Exception as e:
            logger.error('prune_old_keys failed {}'.format(e))
        while True:
            try:
                store_pingdom_results()
            except Exception as e:
                logger.error('store_pingdom_results failed {}'.format(e))
            try:
                store_newrelic_servers_data(*get_newrelic_servers_data())
            except Exception as e:
                logger.error('store_newrelic_servers_data failed {}'.format(e))
            try:
                store_newrelic_infra_data(*get_newrelic_infra_data())
            except Exception as e:
                logger.error('store_newrelic_infra_data {}'.format(e))
            try:
                store_tick_data(*get_tick_data())
            except Exception as e:
                logger.error('store_tick_data {}'.format(e))
            try:
                store_resource_data('prometheus', *get_prometheus_data())
            except Exception as e:
                logger.error('The following error occured whilst trying to store prometheus data: {}'.format(e))
            try:
                store_sirportly_results()
            except Exception as e:
                logger.error('store_sirportly_results {}'.format(e))
            sleep(refresh_time())

if __name__ == '__main__':
    log_handler = logging.handlers.WatchedFileHandler(warboard_log)
    formatter = logging.Formatter('%(asctime)s: {}.%(name)s: %(levelname)s: %(message)s'.format(warboard_title), '%d-%m-%Y %H:%M:%S')
    log_handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(log_handler)
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logger.setLevel(logging.DEBUG)

    if getpass.getuser() != warboard_user:
        print('Please run the warboard with the correct user: '+warboard_user)
        exit(1)
    daemon = WarboardDaemon(warboard_pid_path)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            logger.info('Warboard backend daemon started!')
            daemon.start()
        elif 'stop' == sys.argv[1]:
            logger.info('Warboard backend daemon stopped!')
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            logger.info('Warboard backend daemon restarted!')
            daemon.restart()
        else:
            print('Invalid option!')
            exit(2)
    else:
        print('usage: start|stop|restart')
        exit(2)
