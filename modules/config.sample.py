# Redis details
redis_host = 'localhost'
redis_port = 6379
redis_db = 0

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

# NewRelic details
newrelic_endpoint = 'https://api.newrelic.com/v2/servers.json'
newrelic_timeout = 10 # How long the warboard should wait on the newrelic API
# All you need for adding newrelic accounts is the API key.
# You can split the account name with a pipe '|' for a subcustomer, support for this will be added in future versions. e.g account1|subcustomer
newrelic_keys = {'account1': 'api_key',
                 'account2': 'api_key',
                 'account3': 'api_key',
                 'account1|subcustomer': 'api_key',}

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
sirportly_greenuser_filter = '30'
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
