import requests
import json
import time
from misc import log_messages, chain_results
from config import insights_endpoint, infra_query, insights_timeout, insights_keys

def store_newrelic_infra_data():
    """
    Calls get_infra_data and puts the relavent structured data into redis
    """
    infra_results = {}
    infra_results['red'] = 0
    infra_results['orange'] = 0
    infra_results['green'] = 0
    infra_results['blue'] = 0
    infra_results['failed_accounts'] = 0
    infra_results['successful_checks'] = 0
    for account in insights_keys:
        account_results = []
        url = '{}{}{}'.format(insights_endpoint, insights_keys[account]['account_number'], infra_query)
        infra_results[account] = None
        try:
            r = requests.get(url, headers={'X-Query-Key': insights_keys[account]['api_key']}, timeout=insights_timeout)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            infra_results['failed_accounts'] += 1
            log_messages('Could not get NewRelic Infrastructure data for {} error'.format(account))
            continue

        account_infra_data = json.loads(r.text)

        # The newrelic insights api returns multiple timestamps with thier own
        # data for each api call, we are only interested in the latest one per
        # host which will all be the same timestamp the next section gets that
        # timestamp

        # I would like to compare the timestamp to the system's time
        # however I don't like the format newrelic gives them in and can't see
        # they are handling timezones / decide how I would
        latest_timestamp == 0
        for num, host_data in enumerate(account_infra_data['results'][0]['events']):
            if account_infra_data['results'][0]['events'][num]['timestamp'] >= latest_timestamp:
                latest_timestamp = account_infra_data['results'][0]['events'][num]['timestamp']

        # This is only likely to occur when newrelic insights hasn't returned
        # any host data but has still passed all of the headers I can get this
        # by passing time of 1 seconds instead of 30 and suspect that if no
        # servers are reporting in we would also do
        # The response looks like:
        """
        u'{"results":[{"events":[]}],"performanceStats":{"fileReadCount":1,"decompressionCount":0,"decompressionCacheEnabledCount":0,"inspectedCount":8815,"omittedCount":0,"matchCount":0,"processCount":1,"rawBytes":1573552,"decompressedBytes":1573552,"ioBytes":1573552,"decompressionOutputBytes":0,"responseBodyBytes":161,"fileProcessingTime":1,"mergeTime":0,"ioTime":1,"decompressionTime":0,"decompressionCacheGetTime":0,"decompressionCachePutTime":0,"wallClockTime":8,"fullCacheHits":0,"partialCacheHits":0,"cacheMisses":0,"cacheSkipped":1,"maxInspectedCount":8815,"minInspectedCount":8815,"slowLaneFiles":0,"slowLaneFileProcessingTime":0,"slowLaneWaitTime":0,"sumSubqueryWeight":1.0,"sumFileProcessingTimePercentile":0.0,"subqueryWeightUpdates":0,"sumSubqueryWeightStartFileProcessingTime":13,"runningQueriesTotal":2,"ignoredFiles":0},"metadata":{"eventTypes":["SystemSample"],"eventType":"SystemSample","openEnded":true,"beginTime":"2017-09-08T16:43:15Z","endTime":"2017-09-08T16:43:16Z","beginTimeMillis":1504888995663,"endTimeMillis":1504888996663,"rawSince":"1 SECONDS AGO","rawUntil":"`now`","rawCompareWith":"","guid":"fd637d85-75dd-322a-3f4f-d6d4cfa7e5bf","routerGuid":"c0fd1652-bd5b-cb50-69e8-5674130dbcff","messages":[],"contents":[{"function":"events","limit":10,"columns":["displayName","fullHostname","cpuPercent","memoryUsedBytes","memoryTotalBytes","diskUtilizationPercent","diskUsedPercent","timestamp"],"order":{"column":"timestamp","descending":true}}]}}'
        """
        if latest_timestamp == 0:
            infra_results['failed_accounts'] += 1
            log_messages('Did not recieve NewRelic Infrastructure data for {} error'.format(account))
            continue

        # Filter down to only the latest timestamp
        for num, host_data in enumerate(account_infra_data['results'][0]['events']):
            if account_infra_data['results'][0]['events'][num]['timestamp'] != latest_timestamp:
                continue

            infrastructure_host = {}
            # name is the display name, if it is not set it is the hostname
            infrastructure_host['name'] = account_infra_data['results'][0]['events'][num]['fullHostname']
            if account_infra_data['results'][0]['events'][num]['displayName']:
                infrastructure_host['name'] = account_infra_data['results'][0]['events'][num]['displayName']

            # data we are interested in needs to be in a format similar to
            # newrelic servers in order to easily be displayed along side it
            infrastructure_host['summary'] = {
                'memory': ( account_infra_data['results'][0]['events'][num]['memoryUsedBytes'] / account_infra_data['results'][0]['events'][num]['memoryTotalBytes'] ) * 100,
                'disk_io': account_infra_data['results'][0]['events'][num]['diskUtilizationPercent'],
                'fullest_disk': account_infra_data['results'][0]['events'][num]['diskUsedPercent'],
                'cpu': account_infra_data['results'][0]['events'][num]['cpuPercent'] }

            # The warboard script will check this was in the last 5 minutes
            # and react acordingly - set to blue order by 0
            # The warboard will need to have a list of hosts and check if they
            # are no-longer present since this will be overwriting the key in
            # when it gets a response for half of the hosts/accounts
            infrastructure_host['latest_update'] = time.time()

            # Setting the orderby using the same field as newrelic servers
            infrastructure_host['orderby'] = max(
                    infrastructure_host['summary']['cpu'],
                    infrastructure_host['summary']['memory'],
                    infrastructure_host['summary']['fullest_disk'],
                    infrastructure_host['summary']['disk_io'])

            # Servers returns this, I can't see how to get it out of the
            # insights api to check if a server has exceeded warning and alert
            # thresholds we could make a call to the infrastructure api
            # however this is not a priority, for now all health_status's
            # are set based on order by where > 80 is red and > 60 is orange
            # this is disabled since we don't want it
            if infrastructure_host['orderby'] > 100:
                infrastructure_host['health_status'] = 'red'
                infra_results['red'] += 1
            elif infrastructure_host['orderby'] > 100:
                infrastructure_host['health_status'] = 'orange'
                infra_results['orange'] += 1
            elif: infrastructure_host['orderby'] == 0:
                infrastructure_host['health_status'] = 'blue'
                infra_results['blue'] += 1
            else:
                infrastructure_host['health_status'] = 'green'
                infra_results['green'] += 1

            infra_results['successful_checks'] += 1
            account_results.append(infrastructure_host)

        set_data('newrelic_infra_'+account, account_results)

    set_data('newrelic_infrastructure', infra_results)

def get_newrelic_infra_results():
    """
    Pulls Infrastructure data from redis and checks for missing hosts/accounts
    and formats it ready to be merged with other resource modules by the calling
    function
    """
    all_infra_results = []
    infra_results = {}
    for account in insights_keys:
        result_json = json.loads(get_data('infra_{}'.format(account)))
        all_infra_results.append(result_json)

    # This is likely all broken and irrelevant
    infra_results['total_infra_accounts'] = int(get_data('total_infra_accounts'))
    infra_results['failed_infra'] = int(get_data('failed_infra'))
    infra_results['working_infra'] = infra_results['total_infra_accounts']-infra_results['failed_infra']
    infra_results['working_percentage'] = int(float(infra_results['working_infra'])/float(infra_results['total_infra_accounts'])*100)
    infra_results['checks'] = chain_results(all_results) # Store all the NewRelic Infrastructure results as 1 chained list
    infra_results['total_checks'] = len(infra_results['checks'])
    infra_results['green'] = 0
    infra_results['red'] = 0
    infra_results['orange'] = 0
    infra_results['blue'] = 0
    for customer in infra_results['checks']: # Categorize all the checks as up/down and use the highest metric for each item as the thing we order by
        for server in customer['results'][0]['events']:
            name = server['fullHostname']
            if server['displayName'] != None:
                name = server['displayName']

            name = name[:30] # Limit NewRelic Infrastructure server names to 30 characters to not break the warboard layout
            # not sure how this is handeling servers that are not reporting
            #####I am leaving this here for a minute
            check['orderby'] = max(check['summary']['cpu'], check['summary']['memory'], check['summary']['fullest_disk'], check['summary']['disk_io'])
            if check['health_status'] == 'green':
                newrelic_results['green'] +=1
            elif check['health_status'] == 'orange':
                newrelic_results['orange'] +=1
            elif check['health_status'] == 'red':
                newrelic_results['red'] +=1

        elif check['reporting'] == False:
            check['orderby'] = 0
            check['health_status'] = 'blue'
            newrelic_results['blue'] +=1

    newrelic_results['red_percent'] = math.ceil(100*float(newrelic_results['red'])/float(newrelic_results['total_checks']))
    newrelic_results['green_percent'] = math.ceil(100*float(newrelic_results['green'])/float(newrelic_results['total_checks']))
    newrelic_results['orange_percent'] = math.ceil(100*float(newrelic_results['orange'])/float(newrelic_results['total_checks']))
    newrelic_results['blue_percent'] = 100-newrelic_results['red_percent']-newrelic_results['green_percent']-newrelic_results['orange_percent']
    if newrelic_results['blue_percent'] < 0:
        newrelic_results['green_percent'] = newrelic_results['green_percent']-abs(newrelic_results['blue_percent'])

    return(newrelic_results)
