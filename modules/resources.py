from __future__ import division
from newrelic_servers import get_newrelic_servers_results
from newrelic_infrastructure import get_newrelic_infra_results
from misc import chain_results
from config import newrelic_servers_keys, newrelic_insights_keys

def get_resource_results():
    """
    Merges lists returned by resource modules into one list in the correct
    format for warboard.html to display monitored resources

    {% for check in resource_results['checks']|sort(attribute='orderby')|reverse %}

    <tr class="danger lead"><td>{{ check['name'] }}</td><td>{{ check['summary']['cpu'] }}%</td><td>{{ check['summary']['memory'] }}%</td><td>{{ check['summary']['disk_io'] }}%</td><td>{{ check['summary']['fullest_disk'] }}%</td></tr>

    """
    resource_results = {}
    resource_results['green'] = 0
    resource_results['red'] = 0
    resource_results['orange'] = 0
    resource_results['blue'] = 0
    resource_results['total_accounts'] = 0
    resource_results['checks'] = []

    if newrelic_servers_keys:
        newrelic_servers_results = get_newrelic_servers_results()
        resource_results['green'] += newrelic_servers_results['green']
        resource_results['red'] += newrelic_servers_results['red']
        resource_results['orange'] += newrelic_servers_results['orange']
        resource_results['blue'] += newrelic_servers_results['blue']
        resource_results['checks'] = {**resource_results['checks'], **newrelic_servers_results['checks'])}

#    if newrelic_insights_keys:
#        newrelic_infra_results = get_newrelic_infra_results()
#        resource_results['green'] += newrelic_infra_results['green']
#        resource_results['red'] += newrelic_infra_results['red']
#        resource_results['orange'] += newrelic_infra_results['orange']
#        resource_results['blue'] += newrelic_infra_results['blue']
#        chain_results(resource_results['checks'], newrelic_infra_results['checks'])

    total_results = resource_results['green'] + resource_results['red'] + resource_results['orange'] + resource_results['blue']
    resource_results['red_percent'] = ( resource_results['red'] / total_results ) * 100
    resource_results['orange_percent'] = ( resource_results['red'] / total_results ) * 100
    resource_results['blue_percent'] = ( resource_results['red'] / total_results ) * 100
    # I want the percentage to always be 100 and green seems the most disposable and least affected by any rounding issues
    resource_results['green_percent'] = 100 - ( resource_results['red_percent'] + resource_results['orange_percent'] + resource_results['blue_percent'] )

    newrelic_results['working_newrelic'] = newrelic_results['total_newrelic_accounts']-newrelic_results['failed_newrelic']
    newrelic_results['working_percentage'] = int(float(newrelic_results['working_newrelic'])/float(newrelic_results['total_newrelic_accounts'])*100)

    return resource_results
