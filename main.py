#!/usr/bin/env python3
from flask import Flask, request, render_template, jsonify
import logging
import logging.handlers
import logging.config
from modules.misc import refresh_time
from modules.config import sirportly_users, sirportly_user_order, warboard_stats_key, warboard_log, warboard_title, resources_max_name_length, latency_max_name_length
from modules.port_monitoring import get_port_monitoring_results
from modules.resources import get_resource_results
from modules.sirportly import get_sirportly_results
from modules.calendar_functions import get_calendar_items

## TODO:
# Implement logging inside modules to a greater extent
#
# Set a data age on monitored data - pingdom
#
# Staging flag to store in a different database so testing can be done on the
# live server without interfering with the live warboard
#

logger = logging.getLogger(__name__)
# We are declaring an almost identical dict twice and hardcoding
# webserver and daemon into the name.  This will need improving
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,  # this fixes the problem
    'formatters': {
        'standard': {
            'format': '%(asctime)s: warboard_webserver.%(name)s: %(levelname)s: %(message)s',
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

app = Flask(__name__)

@app.route('/', methods=['GET'])
def warboard():
    logger.debug('Serving warboard')
    return(render_template('warboard.html',
        title=warboard_title,
        refresh_time=refresh_time(),
        port_results=get_port_monitoring_results(),
        latency_max_name_length=latency_max_name_length,
        resource_results=get_resource_results(),
        resources_max_name_length=resources_max_name_length,
        sirportly_results=get_sirportly_results(),
        sirportly_users=sirportly_users,
        sirportly_user_order=sirportly_user_order,
        calendar_items=get_calendar_items()))

@app.route('/shorten', methods=['GET'])
@app.route('/short', methods=['GET'])
def warboard_short():
    logger.debug('Serving shortened warboard')
    port_results = get_port_monitoring_results()
    # As I don't use filters or lambda functions I feel this needs explanation.
    # For the most part we aren't interested in checks that are up.
    # If they are taking more than 2 seconds to return then maybe we are
    # filter runs the function for each check in our list of checks and then
    # returns the list of the ones that it is true for.
    port_results['checks'] = list(filter(lambda x: x['status'] != 'up' or x['lastresponsetime'] > 1000, port_results['checks']))
    return(render_template('warboard.html',
        title=warboard_title,
        refresh_time=refresh_time(),
        port_results=port_results,
        latency_max_name_length=latency_max_name_length,
        resource_results=get_resource_results(),
        resources_max_name_length=resources_max_name_length,
        sirportly_results=get_sirportly_results(),
        sirportly_users=sirportly_users,
        sirportly_user_order=sirportly_user_order,
        calendar_items=get_calendar_items()))

@app.route('/stats', methods=['POST'])
def stats():
    if 'key' not in request.form:
        return(jsonify(status='error',
            message='API Key required')), 401
    if request.form['key'] == warboard_stats_key:
        resource_results = get_resource_results()
        port_results = get_port_monitoring_results()
        sp_results = get_sirportly_results()
        # This breaks backwards compatability
        return(jsonify(status='ok',
            resolved_tickets=sp_results['resolved_tickets'],
            unassigned_tickets=sp_results['unassigned_tickets'],
            waitingstaff_tickets=sp_results['waitingstaff_tickets'],
            latency_checks_total=port_results['total_checks'],
            latency_checks_up=port_results['up'],
            latency_checks_down=port_results['down'],
            latency_checks_paused=port_results['paused'],
            latency_accounts_total=port_results['total_accounts'],
            latency_accounts_failed=port_results['failed_accounts'],
            latency_accounts_working=port_results['working_accounts'],
            resource_checks_total=resource_results['total_checks'],
            resource_accounts_total=resource_results['total_accounts'],
            resource_accounts_failed=resource_results['failed_accounts'],
            resource_accounts_working=resource_results['working_accounts']))
    else:
        return(jsonify(status='error',
            message='Invalid Key')), 401

if __name__ == '__main__': # Used for testing on servers without an uwsgi/nginx setup
    app.run(debug=True)
