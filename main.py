from flask import Flask, request, render_template, jsonify
from modules.misc import refresh_time
from modules.config import sirportly_users, sirportly_user_order, warboard_stats_key, warboard_title
from modules.pingdom import get_pingdom_results
from modules.newrelic import get_newrelic_results
from modules.sirportly import get_sirportly_results
from modules.calendar_functions import get_calendar_items

app = Flask(__name__)
app.debug = True

@app.route('/', methods=['GET'])
def warboard():
    return(render_template('warboard.html',
        title=warboard_title,
        refresh_time=refresh_time(),
        pingdom_results=get_pingdom_results(),
        newrelic_results=get_newrelic_results(),
        sirportly_results=get_sirportly_results(),
        sirportly_users=sirportly_users,
        sirportly_user_order=sirportly_user_order,
        calendar_items=get_calendar_items()))

@app.route('/stats', methods=['POST'])
def stats():
    if request.form['key'] == warboard_stats_key:
        return(jsonify(status='ok',
            pingdom_count=get_pingdom_results()['total_checks'],
            newrelic_count=get_newrelic_results()['total_checks'],
            resolved_tickets=get_sirportly_results()['resolved_tickets']))
    else:
        return(jsonify(status='error',
            message='Invalid Key')), 403

if __name__ == '__main__': # Used for testing on servers without an uwsgi/nginx setup
    app.run(host='0.0.0.0', debug=True)
