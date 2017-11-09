import requests
import json
import time
from redis_functions import set_data, get_data
from misc import log_messages
from config import influx_read_users, influx_max_data_age

def store_tick_data():
    """
    Collects data for all newrelic infrastructure accounts provided in the
    config file and stores it in redis as json with a key per server with value:
    '[{"orderby": 0, "health_status": "green", "name": "wibble", "summary": {"cpu": 0, "fullest_disk": 0, "disk_io": 0, "memory": 0}}]'
    """
    tick_results = {}
    # This module is written with the assumption that you only have one
    # influx instance to get data from and that the user reading from that
    # instance will have read permissions to every database that is to be
    # displayed from.
    tick_results['failed_accounts'] = 0
    tick_results['total_accounts'] = 0
    tick_results['total_checks'] = 0
    tick_results['successful_checks'] = 0
    for influx_user in influx_read_users:
        # Go and list the databases
        for database in list_of_databases:
            # Go and list the hosts
            for host in list_of_hosts:
                # Go and get metric data for cpu, fullest_disk, disk_io, memory

                # Calculate orderby

                # When set-up go and get the health_status for now it will be
                # green for all hosts

                # Format the data as required and place into redis
