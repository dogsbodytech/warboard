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

    queries = {}
    # Node cpu is a number of cpu cycles so we need to look at the rate
    # to calculate the cpu usage percentage, we previously used the last 1
    # minute but have changed it to 10 to avoid missing data.  If having
    # the very latest data is crucial we could get the last minute and the
    # last 10 minutes and then use the last minute where possible, for now this
    # doesn't seem necessary
    # We are using irate over rate as it seems more suitable for the speed
    # cpu usage will be changing at:
    # https://prometheus.io/docs/prometheus/latest/querying/functions/
    queries['cpu'] = '(1 - avg(irate(node_cpu{mode="idle"}[10m])) by (instance)) * 100'
    queries['memory'] = '((node_memory_MemTotal - node_memory_MemFree) / node_memory_MemTotal) * 100'
    # We want all data for each instance
    # We are only interested in the disk with greatest disk io
    # We are calculating disk io for each disk in the same way as cpu
    queries['disk_io'] = 'max(avg(irate(node_disk_io_time_ms[10m])) by (instance, device)) by (instance)'
    # We need want to exclude temporary file systems, docker and rootfs as it
    # is reported as well as the device that it is mounted on
    # Including just ext4 and vfat covers all the systems we currently want
    # but could easily be wrong in the future or in a different enviroment
    # I'm going to test it like this and consider what a good exclude line
    # would be or how we want to be notified of unexpected data
    queries['fullest_disk'] = 'max(((node_filesystem_size{fstype=~"ext4|vfat"} - node_filesystem_free{fstype=~"ext4|vfat"}) / node_filesystem_size{fstype=~"ext4|vfat"}) * 100) by (instance)'

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
                    prometheus_validity['total_checks'] += 1
                    prometheus_data[user][hostname] = {}
                    # Don't display the prometheus port in the name
                    prometheus_data[user][hostname]['name'] = hostname.rstrip(':9100')
                    prometheus_data[user][hostname]['summary'] = {}

                prometheus_data[user][hostname]['summary'][metric] = float(instance_data['value'][1])

        for host in prometheus_data[user]:
            # IMPROVE
            # we will need to check alerting to calculate health status but that
            # is a second job for after the current code runs propperly
            prometheus_data[user][host]['health_status'] = 'green'
            values = []
            for metric in prometheus_data[user][host]['summary']:
                values.append(metric)

            if len(values) != len(queries):
                prometheus_data[user][host]['orderby'] = 0
                prometheus_data[user][host]['health_status'] = 'blue'
                log_messages('{} only returned data for the following metrics {}'.format(host, values), 'warning')
            else:
                prometheus_data[user][host]['orderby'] = max(values)

    prometheus_validity['valid_until'] = time.time() * 1000 + 300000
    return prometheus_data, prometheus_validity
