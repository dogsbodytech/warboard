from __future__ import division
import json
import time
from redis_functions import get_data, get_all_data, set_data
import logging
logger = logging.getLogger(__name__)

def get_port_monitoring_results():
    port_monitoring_results = {}
    port_monitoring_results['checks'] = []
    port_monitoring_results['total_checks'] = 0
    port_monitoring_results['up'] = 0
    port_monitoring_results['down'] = 0
    port_monitoring_results['paused'] = 0
    port_monitoring_results['total_accounts'] = 0
    port_monitoring_results['failed_accounts'] = 0
    port_monitoring_results['working_accounts'] = 0
    port_monitoring_results['working_percentage'] = 0
    port_monitoring_results['up_percent'] = 0
    port_monitoring_results['down_percent'] = 0
    port_monitoring_results['paused_percent'] = 0
    for module in get_all_data('port_monitoring:*'):
        module_json = get_data(module)
        module_checks = json.loads(module_json)[0]
        port_monitoring_results['checks'] += module_checks

    for module in get_all_data('port_monitoring_success:*'):
        module_json = get_data('module')
        module_success = json.loads(module_json)[0]
        port_monitoring_results['up'] += module_success['up']
        port_monitoring_results['down'] += module_success['down']
        port_monitoring_results['paused'] += module_success['paused']
        port_monitoring_results['total_accounts'] += module_success['total_accounts']
        # All data for each module is stored in one redis key.  If that
        # key is stale then we consider all accounts that module reports
        # as failed
        if module_success['valid_until'] < time.time() * 1000:
            port_monitoring_results['failed_accounts'] += module_success['total_accounts']
        else:
            port_monitoring_results['failed_accounts'] += module_success['failed_accounts']

    port_monitoring_results['total_checks'] = len(port_monitoring_results['checks'])
    port_monitoring_results['down_percent'] = (port_monitoring_results['down'] / port_monitoring_results['total_checks']) * 100
    port_monitoring_results['paused_percent'] = (port_monitoring_results['up'] / port_monitoring_results['total_checks']) * 100
    # Artificially forcing percentages to add up to 100%
    port_monitoring_results['up_percent'] = 100 - (port_monitoring_results['down_percent'] + port_monitoring_results['paused_percent'])
    port_monitoring_results['working_accounts'] = port_monitoring_results['total_accounts'] - port_monitoring_results['failed_accounts']
    port_monitoring_results['working_percentage'] = (port_monitoring_results['working_accounts'] / port_monitoring_results['total_accounts']) * 100
    return port_monitoring_results

def store_port_monitoring_results(module, module_data, module_validity):
    # we are storing everything inside an extra list so we can take it
    # out of that list when we pull it out of redis - don't ask
    set_data('port_monitoring:{}'.format(module), json.dumps([module_data]))
    set_data('port_monitoring_success:{}'.format(module), json.dumps([module_validity]))
