import json
from redis_functions import get_all_data, get_data
from newrelic_servers import get_newrelic_servers_data
from newrelic_infrastructure import get_newrelic_infra_data
from tick import get_tick_data

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

    newrelic_servers_data, newrelic_servers_data_validity = get_newrelic_servers_data()
    for host in newrelic_servers_data:
        host_data = newrelic_servers_data[host]
        reporting_servers.add(host_data['name'])

    newrelic_infra_data, newrelic_infra_data_validity = get_newrelic_infra_data()
    for host in newrelic_infra_data:
        host_data = newrelic_infra_data[host]
        reporting_servers.add(host_data['name'])

    return found_servers - reporting_servers

if __name__ == '__main__':
    print("The following servers aren't reporting:")
    for server in list_unreporting_servers():
        print(server)
