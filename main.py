from flask import Flask, request, render_template, jsonify
import logging
import logging.handlers
from modules.config import warboard_log, warboard_title
from modules.misc import refresh_time
from modules.config import sirportly_users, sirportly_user_order, warboard_stats_key, warboard_title, resources_max_name_length, latency_max_name_length
from modules.pingdom import get_pingdom_results
from modules.resources import get_resource_results
from modules.sirportly import get_sirportly_results
from modules.calendar_functions import get_calendar_items

log_handler = logging.handlers.WatchedFileHandler(warboard_log)
formatter = logging.Formatter('%(asctime)s: {}.%(name)s: %(levelname)s: %(message)s'.format(warboard_title), '%d-%m-%Y %H:%M:%S')
log_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logging.getLogger('requests').setLevel(logging.CRITICAL)
logger.setLevel(logging.DEBUG)

## TODO:
# Improve error logging
#
# Set a data age on monitored data - pingdom
#
# Staging flag to store in a different database so testing can be done on the
# live server without interfering with the live warboard

app = Flask(__name__)

@app.route('/', methods=['GET'])
def warboard():
    return(render_template('warboard.html',
        title=warboard_title,
        refresh_time=refresh_time(),
        pingdom_results=get_pingdom_results(),
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
        pd_results = get_pingdom_results()
        sp_results = get_sirportly_results()
        # This breaks backwards compatability
        return(jsonify(status='ok',
            resolved_tickets=sp_results['resolved_tickets'],
            unassigned_tickets=sp_results['unassigned_tickets'],
            latency_checks_total=pd_results['total_checks'],
            latency_checks_up=pd_results['pingdom_up'],
            latency_checks_down=pd_results['pingdom_down'],
            latency_checks_paused=pd_results['pingdom_paused'],
            latency_accounts_total=pd_results['total_pingdom_accounts'],
            latency_accounts_failed=pd_results['failed_pingdom'],
            latency_accounts_working=pd_results['working_pingdom'],
            resource_checks_total=resource_results['total_checks'],
            resource_accounts_total=resource_results['total_accounts'],
            resource_accounts_failed=resource_results['failed_accounts'],
            resource_accounts_working=resource_results['working_accounts']))
    else:
        return(jsonify(status='error',
            message='Invalid Key')), 401

if __name__ == '__main__': # Used for testing on servers without an uwsgi/nginx setup
    app.run(debug=True)
