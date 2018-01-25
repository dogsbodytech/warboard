import requests
from requests.auth import HTTPBasicAuth
import json
import time
from misc import log_messages
from config import prometheus_credentials

def get_prometheus_data():
    """
    Collects data for all prometheus users provided in the config file and
    returns it as a tuple, dictionary containing all servers as key server
    name, value server data and dictionary with meta data for checks returned
    """
    prometheus_data = {}
    prometheus_validity = {}
    prometheus_validity['failed_accounts'] = 0
    prometheus_validity['total_accounts'] = 0
    prometheus_validity['total_checks'] = 0
    # successful_checks will be removed but it needs to be removed in multiple
    # places at once
    prometheus_validity['successful_checks'] = 0

    queries = {}
    # Node cpu is a number of cpu cycles so we need to look at the rate
    # to calculate the cpu usage percentage
    # We are using irate over rate as it seems more suitable for the speed
    # cpu usage will be changing at:
    # https://prometheus.io/docs/prometheus/latest/querying/functions/
    queries['cpu'] = '(1 - avg(irate(node_cpu{mode="idle"}[1m])) by (instance)) * 100'
    queries['memory'] = '((node_memory_MemTotal - node_memory_MemAvailable) / node_memory_MemTotal) * 100'
    # We want all data for each instance
    # We are only interested in the disk with greatest disk io
    # We are calculating disk io for each disk in the same way as cpu
    queries['disk_io'] = 'max(avg(irate(node_disk_io_time_ms[1m])) by (instance, device)) by (instance)'
    # We need want to exclude temporary file systems, docker and rootfs as it
    # is reported as well as the device that it is mounted on
    # Including just ext4 and vfat covers all the systems we currently want
    # but could easily be wrong in the future or in a different enviroment
    # I'm going to test it like this and consider what a good exclude line
    # would be or how we want to be notified of unexpected data
    queries['disk_space'] = '((node_filesystem_size{fstype=~"ext4|vfat"} - node_filesystem_free{fstype=~"ext4|vfat"}) / node_filesystem_size{fstype=~"ext4|vfat"}) * 100'


    """
    Will need to parse the data before returning it
    Will need to store the data in redis, it would be nice to make a resources
    store data function since it will be almost identical to the other functions
    all that would need to be added would be a name parameter.
    Would like to get alerting status from the alerts section, will do this
    after
    Total checks needs to be used to allow propper api output, since
    successful_checks has been scrapped in favour of using alerting data this
    is a fairly minor thing to add
    """

    for user in prometheus_credentials:
        prometheus_data[user] = {}
        prometheus_validity['total_accounts'] += 1
        responses = {}
        for query in queries:
            try:
                metrics_response = requests.get(
                    '{}/api/v1/query'.format(prometheus_credentials[user]['url']),
                    auth=HTTPBasicAuth(prometheus_credentials[user]['username'],
                    prometheus_credentials[user]['password']),
                    params={'query': queries[query]},
                    timeout=prometheus_credentials[user]['timeout'])
                metrics_response.raise_for_status()
            except requests.exceptions.RequestException as e:
                log_messages('Could not get prometheus data for {}: Error: {}'.format(user, e), 'error')
                continue

            responses[query] = json.loads(metrics_response.text)

        if len(responses) < len(queries):
            prometheus_validity['failed_accounts'] += 1
            continue

        for metric in responses:
            if responses[metric]['status'] != "success":
                continue

            for instance_data in responses[metric]['data']['result']:
                hostname = instance_data['metric']['instance']
                if hostname not in prometheus_data[user]:
                    prometheus_data[user][hostname] = {}
                    prometheus_data[user][hostname]['name'] = hostname
                    prometheus_data[user][hostname]['summary'] = {}

                prometheus_data[user][hostname]['summary'][metric] = instance_data['value'][1]

        for host in prometheus_data[user]:
            values = []
            for metric in prometheus_data[user][host]['summary']:
                values.append(prometheus_data[user][host]['summary'][metric])

            prometheus_data[user][host]['orderby'] = max(values)

            # we will need to check alerting to calculate health status but that
            # is a second job for after the current code runs propperly
            prometheus_data[user][host]['health_status'] = 'green'

    prometheus_validity['valid_until'] = time.time() * 1000 + 300000
    return prometheus_data, prometheus_validity
