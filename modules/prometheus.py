import requests
from requests.auth import HTTPBasicAuth
import json
import time
from modules.config import prometheus_credentials
import logging
logger = logging.getLogger(__name__)

def get_alerting_servers(user):
    """
    Returns a tuple containing two dictionaries:
    all alerting servers for a given user
    all down servers for a given user
    key = server name
    value = list of firing alerts as an integer, 1 is warning, 2 is critical
    """
    alerting_servers = {}
    down_servers = []
    username = prometheus_credentials[user].get('alert_username', prometheus_credentials[user]['username'])
    password = prometheus_credentials[user].get('alert_password', prometheus_credentials[user]['password'])
    try:
        alerting_servers_response = requests.get(
            '{}/api/v1/alerts'.format(prometheus_credentials[user]['alert_url']),
            auth=HTTPBasicAuth(username, password),
            timeout=prometheus_credentials[user]['timeout'])
        alerting_servers_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error('Could not get prometheus alert data for {}: Error: {}'.format(user, e))
        raise

    alerting_servers_json = alerting_servers_response.json()
    try:
        assert alerting_servers_json['status'] == 'success', 'Could not get prometheus alert data for {}: Response status was {}'.format(user, alerting_servers_json['status'])
        for alert in alerting_servers_json['data']:
            # We can ignore alerts that are not for a specific instance
            if 'instance' not in alert['labels']:
                continue

            for label, value in prometheus_credentials[user].get('ignore_lables', {}).items():
                if alert['labels'].get(label) == value:
                    continue

            hostname = alert['labels']['instance']
            # catch servers that are down
            # only check if node exporter is down
            if alert['labels']['alertname'] == 'service_down' and hostname.endswith(':9100'):
                down_servers.append(hostname)
                continue
            # I'm going to make a set of assumptions
            # Alerts returned in this list are all active, so there is no need to
            # check if they have ended or been acknowledged
            # You have a custom label 'severity' which all alerts will be tagged
            # tagged with where P4 as warnings and P1&P2&P3 are critical alerts
            #
            # We are returning status as an integer so that the most severe alert
            # for each server can easily be grabbed
            if alert['labels']['severity'] == 'P4':
                status = 1
            elif alert['labels']['severity'] == 'P3':
                status = 2
            elif alert['labels']['severity'] == 'P2':
                status = 2
            elif alert['labels']['severity'] == 'P1':
                status = 2
            else:
                logger.warning('Invalid severity returned for {}: {}'.format(hostname, alert['labels']['severity']))
                continue

            if hostname not in alerting_servers:
                alerting_servers[hostname] = []

            alerting_servers[hostname].append(status)
    except Exception as e:
        logger.error('An unexpected error occured whilst getting alert data: {}: The json recieved was: {}'.format(e, alerting_servers_json))
        raise

    return alerting_servers, down_servers

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
    for user in prometheus_credentials:
        alerting_servers = {}
        down_servers = []
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
        queries['cpu'] = '(1 - avg(irate(node_cpu{cpu_mode}[10m])) by (instance{labels_to_filter_based_on})) * 100'
        queries['memory'] = '((node_memory_MemTotal - node_memory_MemFree) / node_memory_MemTotal) * 100'
        # We want all data for each instance
        # We are only interested in the disk with greatest disk io
        # We are calculating disk io for each disk in the same way as cpu
        # The /10 is to convert to seconds (/1000) and then to a percentage
        # (*1000)
        queries['disk_io'] = '(max(avg(irate(node_disk_io_time_ms[10m])) by (instance, device{labels_to_filter_based_on})) by (instance{labels_to_filter_based_on}))/10'
        # We need want to exclude temporary file systems, docker and rootfs as it
        # is reported as well as the device that it is mounted on
        # Including just ext4 and vfat covers all the systems we currently want
        # but could easily be wrong in the future or in a different enviroment
        # I'm going to test it like this and consider what a good exclude line
        # would be or how we want to be notified of unexpected data
        # This is configured in the config file as different set-ups may
        # have different filesystems to monitor.  If no argument is supplied
        # all of the disks will be monitored for each instance.
        queries['fullest_disk'] = 'max((((node_filesystem_size_bytes{fullest_disk_sub} or node_filesystem_size{fullest_disk_sub}) - (node_filesystem_free_bytes{fullest_disk_sub} or node_filesystem_free_bytes{fullest_disk_sub})) / (node_filesystem_size_bytes{fullest_disk_sub} or node_filesystem_size{fullest_disk_sub})) * 100) by (instance{labels_to_filter_based_on})'

        # We will either sub in a blank string or the intermittent_tag
        # depending on if one is present
        labels_to_filter_based_on = ''
        if 'intermittent_tag' in prometheus_credentials[user]:
            labels_to_filter_based_on = ', {}'.format(prometheus_credentials[user]['intermittent_tag'])

        for label in prometheus_credentials[user].get('ignore_lables', {}):
            labels_to_filter_based_on += ', {}'.format(label)

        for query in queries:
            # CPU mode it necessary to avoid it being counted as a key
            # fullest_disk_sub needs to be substituted here or after
            # or it will be counted as a key
            # We are trying to substitute the intermittent_tag into
            # every group by in order to keep the tag
            queries[query] = queries[query].format(labels_to_filter_based_on = labels_to_filter_based_on, cpu_mode = '{mode="idle"}', fullest_disk_sub = prometheus_credentials[user].get('fullest_disk_tags', ''))

        try:
            alerting_servers, down_servers = get_alerting_servers(user)
        except Exception as e:
            logger.error('The following error occured whilst getting the list of alerting servers for {}: {}'.format(user, e))

        #logger.error('Down servers:{}\nAlerting servers{}'.format(down_servers, alerting_servers), 'info')

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
                logger.error('Could not get prometheus data for {}: Error: {}'.format(user, e))
                continue

            responses[query] = json.loads(metrics_response.text)

        #logger.error('Responses: {}'.format(responses), 'info')
        if len(responses) < len(queries):
            prometheus_validity['failed_accounts'] += 1
            continue

        #logger.error('Looping through responses', 'info')
        for metric in responses:
            if responses[metric]['status'] != "success":
                continue

            for instance_data in responses[metric]['data']['result']:
                hostname = instance_data['metric']['instance']
                for label, value in prometheus_credentials[user].get('ignore_lables', {}).items():
                    if instance_data['metric'].get(label) == value:
                        continue

                if hostname not in prometheus_data[user]:
                    prometheus_validity['total_checks'] += 1
                    prometheus_data[user][hostname] = {}
                    # Don't display the prometheus port in the name
                    prometheus_data[user][hostname]['name'] = hostname.rstrip(':9100')
                    prometheus_data[user][hostname]['summary'] = {}

                if 'intermittent_tag' in prometheus_credentials[user]:
                    if instance_data['metric'].get(prometheus_credentials[user]['intermittent_tag']) in prometheus_credentials[user].get('intermittent_true_values', []):
                        prometheus_data[user][hostname]['volatile'] = True

                prometheus_data[user][hostname]['summary'][metric] = float(instance_data['value'][1])

        to_remove = []
        #logger.error('Setting health status and orderby for servers: {}'.format(prometheus_data[user]), 'info')
        for host in prometheus_data[user]:
            # Check if the server is alerting and set the health status
            health_status = 'green'
            if host in alerting_servers:
                alert_level = max(alerting_servers[host])
                if alert_level == 1:
                    health_status = 'orange'
                if alert_level == 2:
                    health_status = 'red'

            prometheus_data[user][host]['health_status'] = health_status
            # Calculate the order by.  If the server isn't reporting every
            # metric flag it as unreporting and log the issue.
            metrics = []
            values = []
            for metric in prometheus_data[user][host]['summary']:
                metrics.append(metric)
                values.append(prometheus_data[user][host]['summary'][metric])

            if len(values) != len(queries):
                # Mark servers to be removed so we don't encounter a
                # run time error due to removing items from a dictionary
                # we are looping through
                to_remove.append(host)
                # If a server is transient this is INFO otherwise WARN
                if prometheus_data[user][host].get('volatile') == True:
                    logger.info('Volatile host {} only returned data for the following metrics {}'.format(host, metrics))
                else:
                    logger.warning('{} only returned data for the following metrics {}'.format(host, metrics))
            else:
                prometheus_data[user][host]['orderby'] = max(values)

        #logger.error('Removing unreporting servers: {}'.format(to_remove), 'info')
        for server_to_remove in to_remove:
            del prometheus_data[user][server_to_remove]

        for host in down_servers:
            if host not in prometheus_data[user]:
                prometheus_validity['total_checks'] += 1
                prometheus_data[user][host] = {}
                prometheus_data[user][host]['name'] = host.rstrip(':9100')
                prometheus_data[user][host]['summary'] = {}

            prometheus_data[user][host]['health_status'] = 'blue'
            prometheus_data[user][host]['orderby'] = 0

    # Data should be considerd stale after 5 minutes
    prometheus_validity['valid_until'] = time.time() * 1000 + 300000
    return prometheus_data, prometheus_validity
