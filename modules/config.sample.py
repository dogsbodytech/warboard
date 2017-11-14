# Redis details
redis_host = 'localhost'
redis_port = 6379
redis_db = 0

# Display details
# It is worth noting the default behavior of the flask truncate filter
# http://jinja.pocoo.org/docs/2.9/templates/#truncate
# Currently it avoids cutting words, gives 5 characters leeway before before
# truncating and then appends ... to any strings that have been truncated
latency_max_name_length = 60
resources_max_name_length = 60

# Pingdom details
pingdom_endpoint = 'https://api.pingdom.com/api/2.0/checks'
pingdom_timeout = 10 # How long the warboard should wait on the pingdom API
# The below example includes 4 pingdom accounts, accounts (2,3,4) are normal pingdom accounts with the accounts apikey/email/password
# Account 1 is an example of how you would do api calls to an account you have admin access on from a separate account, when you don't have login credentials for the account.
# You can split the account name with a pipe '|' for a subcustomer, support for this will be added in future versions. e.g account1|subcustomer
pingdom_multiaccounts = {'account1': {'api_key': 'account1@example.org'}}
pingdom_keys = {'account2': {'api_key': 'account2@example.org:password'},
                'account3': {'api_key': 'account3@example.org:password'},
                'account4': {'api_key': 'account3@example.org:password'},
                'account1': {'api_key_admin': 'adminaccount@example.org:password'}}

# NewRelic Servers details
newrelic_servers_endpoint = 'https://api.newrelic.com/v2/servers.json'
newrelic_servers_timeout = 10 # How long the warboard should wait on the newrelic API
# All you need for adding newrelic accounts is the API key.
# You can split the account name with a pipe '|' for a subcustomer, support for this will be added in future versions. e.g account1|subcustomer
newrelic_servers_keys = {'account1': 'api_key',
                         'account2': 'api_key',
                         'account3': 'api_key',
                         'account1|subcustomer': 'api_key',}

# NewRelic Infrastructure details
# NewRelic Insights api endpoint to pull out NewRelic Infrastructure data
newrelic_insights_endpoint = 'https://insights-api.newrelic.com/v1/accounts/'
newrelic_insights_timeout = 10
# NewRelic api endpoint to pull out current alerting data
newrelic_main_api_violation_endpoint = 'https://api.newrelic.com/v2/alerts_violations.json?only_open=true'
newrelic_main_api_timeout = 10
# Specify how long (seconds) metric data recieved from the newrelic insights
# api is valid for, after this time servers will be shown as not reporting
newrelic_infrastructure_max_data_age = 300
# Two set's of keys are required - one to get the metric data, one to check
# if the servers are alerting
newrelic_main_and_insights_keys =   {'account_name1':  {'account_number': 'number_here',
                                                        'main_api_key': 'key_here',
                                                        'insights_api_key': 'key_here'},
                                     'account_name2':  {'account_number': 'number_here',
                                                        'main_api_key': 'key_here',
                                                        'insights_api_key': 'key_here'}}

# TICK details
# Credentials for a user that has read access to every database you wish to
# monitor telegraf clients on
# If you have multiple users or influx instances to monitor you can list them
# as a list of dictionarys
influx_read_users = [{'influx_url': 'https://example.com:8086',
                      'influx_user': 'username1',
                      'influx_pass': 'password1'},
                     {'influx_url': 'https://example.org:8086',
                      'influx_user': 'username2',
                      'influx_pass': 'password2'}]
# How old (seconds) data can be before a server is considered not reporting
influx_max_data_age = 300
influx_timeout = 10
# Used to reduce the number of queries required when a lot of databases are in
# use
influx_database_batch_size = 40

# Sirportly details
sirportly_endpoint = 'https://sirportly.example.org/api/v2/tickets'
sirportly_token = 'token_here'
sirportly_key = 'key_here'
# These are the filter ID's in sirportly to get the stats needed, info on setting these up is in the Readme.
sirportly_unassigned_filter = '1'
sirportly_resolved_filter = '4'
sirportly_red_filter = '33'
sirportly_total_filter = '27'
sirportly_reduser_filter = '31'
sirportly_greenuser_filter = '58'
sirportly_blueuser_filter = '30'
# The sirportly usernames with a nice name for display on the board
sirportly_users = {'username1': 'User 1',
                   'username2': 'User 2',
                   'username3': 'User 3',
                   'username4': 'User 4',
                   'username5': 'User 5'}
# The order sirportly users will be displayed in on the board
sirportly_user_order = ['username2',
                        'username3',
                        'username1',
                        'username4',
                        'username5']

# Calendar details
# A path to the json calendar export from Google Calendar
calendar_export = '/home/user/calendar/export.json' # Full path to the calendar json file

# Warboard details
# The path to the file the warboard stores errors and messages in
warboard_log = '/home/warboard/logs/warboard.log'
# The API key users should use when using the /stats function of the warboard
warboard_stats_key = 'api_key'
# How many green results should be returned for the Pingdom/NewRelic columns. This can help save on bandwidth/page load time
warboard_result_count = 30
# The title used on the warboard
warboard_title = 'Warboard'
# The file used to store the pid file by the Daemon
warboard_pid_path = '/tmp/warboard_daemon.pid'
# The user you will run the warboard as
warboard_user = 'warboard'
