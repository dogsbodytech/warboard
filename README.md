# Warboard
This is the warboard we use internally at Dogsbody Technology Ltd. The backend is all written in Python and the frontend is Python (Flask) using the Jinja2 templating engine.

##Requirements
The warboard requires you have redis-server, python, python-virtualenv, python-dev, libffi-dev & libssl-dev installed:

```sudo apt-get install redis-server python python-virtualenv python-dev libffi-dev libssl-dev```

Once you have these installed you can create a virtual environment and install the required python modules in the environment:

```virtualenv venv```

```. venv/bin/activate```

```pip install -r requirements.txt```

You will also need to setup some filters in sirportly and record their ID's in your config.py file, first of all copy the config.sample.py file to config.py. The following filters are required:

**sirportly_unassigned_filter** (Matches all these conditions: Assigned user is not blank & Status type is not closed)

**sirportly_resolved_filter** (Matches all these conditions: Status type is closed)

**sirportly_red_filter** (Matches all these conditions: Status type is open, Priority is less than low, Status is not waiting for reply & Status is not internal)

**sirportly_total_filter** (Matches all these conditions: Status type is not closed & Priority is less than low)

**sirportly_reduser_filter** (Matches all these conditions: Assigned user is current user & Priority is less than low. Matches any of these conditions: Status is new & status is
waiting for staff)

**sirportly_greenuser_filter** (Matches all these conditions: Assigned user is current user & Priority is less than low. Matches any of these conditions: Status waiting for reply & status is on hold)
