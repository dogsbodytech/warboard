#!/usr/bin/env python3
import json
from modules.redis_functions import get_all_data, get_data
from modules.newrelic_infrastructure import get_newrelic_infra_data
from modules.prometheus import get_prometheus_data
from modules.tick import get_tick_data
from modules.datadog import get_datadog_data

def list_unreporting_servers():
    found_servers = set()
    for key in get_all_data('resources:*'):
        host_data = json.loads(get_data(key))[0]
        found_servers.add(host_data['name'])

    reporting_servers = set()
    tick_data, tick_data_validity = get_tick_data()
    for host in tick_data:
        host_data = tick_data[host]
        reporting_servers.add(host_data['name'])

    newrelic_infra_data, newrelic_infra_data_validity = get_newrelic_infra_data()
    for host in newrelic_infra_data:
        host_data = newrelic_infra_data[host]
        reporting_servers.add(host_data['name'])

    prometheus_data, prometheus_data_validity = get_prometheus_data()
    for user in prometheus_data:
        for host in prometheus_data[user]:
            host_data = prometheus_data[user][host]
            reporting_servers.add(host_data['name'])

    datadog_data, datadog_data_validity = get_datadog_data()
    for user in datadog_data:
        for host in datadog_data[user]:
            host_data = datadog_data[user][host]
            reporting_servers.add(host_data['name'])

    return found_servers - reporting_servers

if __name__ == '__main__':
    print('Checking unreporting servers this may take around 30 seconds.')
    unreporting = list_unreporting_servers()
    if unreporting:
        print("The following servers aren't reporting:")
        for server in unreporting:
            print("\t'{}'".format(server))
    else:
        print('No unreporting servers found!')

    print('It is recommended that you call this function 3 times to ensure you get a reliable result.')
