# Warboard
This is the warboard we use internally at Dogsbody Technology Ltd. The backend is all written in Python and the frontend is Python (Flask) using the Jinja2 templating engine.

##Requirements
The warboard requires you have redis-server, python, python-virtualenv, python-dev, libffi-dev & libssl-dev installed:

```sudo apt-get install redis-server python python-virtualenv python-dev libffi-dev libssl-dev```

Once you have these installed you can create a virtual environment and install the required python modules in the environment:

```virtualenv venv
. venv/bin/activate
pip install -r requirements.txt```

You will also need to setup some filters in sirportly and record their ID's in your config.py file, first of all copy the config.sample.py file to config.py.
