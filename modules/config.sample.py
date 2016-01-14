# Redis details
redis_host = 'localhost'
redis_port = '6379'
redis_db = '0'

# Pingdom details
pingdom_endpoint = 'https://api.pingdom.com/api/2.0/checks'
pingdom_timeout = 10 # How long the warboard should wait on the pingdom API
pingdom_keys = {}
pingdom_multiaccounts = {} # This is required if you're doing API requests with your own pingdom account on another pingdom account.

# NewRelic details
newrelic_endpoint = 'https://api.newrelic.com/v2/servers.json'
newrelic_timeout = 10 # How long the warboard should wait on the newrelic API
newrelic_keys = {}

# Sirportly details
sirportly_endpoint = 'https://sirportly.example.org/api/v2/tickets'
sirportly_token = ''
sirportly_key = ''

# Calendar details
calendar_export = '' # Full path to the calendar json file


# REBUILD THIS ONCE I HAVE FINISHED THE CURRENT CONFIG FILE
