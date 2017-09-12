from flask import Flask, request, render_template, jsonify
from modules.misc import refresh_time
from modules.config import sirportly_users, sirportly_user_order, warboard_stats_key, warboard_title, resources_max_name_length, resources_cpu_max_figures, resources_memory_max_figures, resources_disk_io_max_figures, resources_fullest_disk_max_figures
from modules.pingdom import get_pingdom_results
from modules.resources import get_resource_results
from modules.sirportly import get_sirportly_results
from modules.calendar_functions import get_calendar_items

app = Flask(__name__)

@app.route('/', methods=['GET'])
def warboard():
    return(render_template('warboard.html',
        title=warboard_title,
        refresh_time=refresh_time(),
        pingdom_results=get_pingdom_results(),
        resource_results=get_resource_results(),
        resources_max_name_length=resources_max_name_length,
        resources_cpu_max_figures=resources_cpu_max_figures,
        resources_memory_max_figures=resources_memory_max_figures,
        resources_disk_io_max_figures=resources_disk_io_max_figures,
        resources_fullest_disk_max_figures=resources_fullest_disk_max_figures,
        sirportly_results=get_sirportly_results(),
        sirportly_users=sirportly_users,
        sirportly_user_order=sirportly_user_order,
        calendar_items=get_calendar_items()))

"""
@app.route('/stats', methods=['POST'])
def stats():
    if 'key' not in request.form:
        return(jsonify(status='error',
            message='API Key required')), 401
    if request.form['key'] == warboard_stats_key:
        nr_results = get_newrelic_results()
        pd_results = get_pingdom_results()
        sp_results = get_sirportly_results()
        return(jsonify(status='ok',
            pingdom_count=pd_results['total_checks'],
            newrelic_count=nr_results['total_checks'],
            resolved_tickets=sp_results['resolved_tickets'],
            unassigned_tickets=sp_results['unassigned_tickets'],
            pingdom_up=pd_results['pingdom_up'],
            pingdom_down=pd_results['pingdom_down'],
            pingdom_paused=pd_results['pingdom_paused'],
            pingdom_accounts=pd_results['total_pingdom_accounts'],
            pingdom_failed=pd_results['failed_pingdom'],
            pingdom_working=pd_results['working_pingdom'],
            newrelic_accounts=nr_results['total_newrelic_accounts'],
            newrelic_working=nr_results['working_newrelic'],
            newrelic_failed=nr_results['failed_newrelic']))
    else:
        return(jsonify(status='error',
            message='Invalid Key')), 401
"""

if __name__ == '__main__': # Used for testing on servers without an uwsgi/nginx setup
    app.run(debug=True)
