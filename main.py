from flask import Flask, request, render_template, jsonify
from modules.config import sirportly_users, sirportly_user_order
from modules.pingdom import get_pingdom_results
from modules.newrelic import get_newrelic_results
from modules.sirportly import get_sirportly_results
from modules.calendar_functions import get_calendar_items

app = Flask(__name__)

@app.route('/', methods=['GET'])
def warboard():
    return(render_template('warboard.html',
        pingdom_results=get_pingdom_results(),
        newrelic_results=get_newrelic_results(),
        sirportly_results=get_sirportly_results(),
        sirportly_users=sirportly_users,
        sirportly_user_order=sirportly_user_order,
        calendar_items=get_calendar_items()))

if __name__ == '__main__':
    app.run(debug=True)
