# Warboard
This is the warboard we use internally at Dogsbody Technology Ltd. The backend is all written in Python and the frontend is Python (Flask) using the Jinja2 templating engine.

##Requirements
The warboard requires you have redis-server, python, python-virtualenv, python-dev, libffi-dev & libssl-dev installed:

```sudo apt-get install redis-server python python-virtualenv python-dev libffi-dev libssl-dev```

Once you have these installed you can create a virtual environment and install the required python modules in the environment:

```
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

You will also need to setup some filters in sirportly and record their ID's in your config.py file, first of all copy the config.sample.py file to config.py.

The following filters are required:

- sirportly_unassigned_filter (Matches all these conditions: Assigned user is not blank & Status type is not closed)

- sirportly_resolved_filter (Matches all these conditions: Status type is closed)

- sirportly_red_filter (Matches all these conditions: Status type is open, Priority is less than low, Status is not waiting for reply & Status is not internal)

- sirportly_total_filter (Matches all these conditions: Status type is not closed & Priority is less than low)

- sirportly_reduser_filter (Matches all these conditions: Assigned user is current user & Priority is less than low. Matches any of these conditions: Status is new & status is
waiting for staff)

- sirportly_greenuser_filter (Matches all these conditions: Assigned user is current user & Priority is less than low. Matches any of these conditions: Status waiting for reply & status is on hold)

The rest of the settings in the config file should also be filled out, the required values should be pretty self explanatory with the examples in the sample config file. Support will be added in the future for enabling and disabling different parts of the Warboard (Pingdom, NewRelic, Sirportly etc).


##Setup
Once the config file has been correctly created all you will need to do is setup a cron running as the warboard user. The cron should contain the following (change the paths if applicable):

```*/15 * * * * /home/warboard/app/crons/check_daemon.sh /home/warboard/app/venv/bin/python /home/warboard/app/modules/daemon.py /home/warboard/app/logs/warboard.log```

This cron will check the backend daemon is running and start it if it's not, make sure the warboard users emails are being delivered somewhere so in a situation where the daemon is broken you will be notified. You can test the warboard in a dev environment by just running the main.py file in the virtual environment. In production nginx & uwsgi should be used.
