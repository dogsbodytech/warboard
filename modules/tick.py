import requests
import json
import time
from redis_functions import set_data, get_data
from misc import log_messages
from config import influx_url, influx_read_user_name, influx_read_user_pass, influx_max_data_age
