// import requests
// import math
// from modules.redis_functions import set_data, get_data
// from modules.config import sirportly_key, sirportly_token, sirportly_users, sirportly_endpoint, sirportly_red_filter, sirportly_blue_filter, sirportly_resolved_filter
// from modules.config import sirportly_total_filter, sirportly_reduser_filter, sirportly_greenuser_filter, sirportly_blueuser_filter, sirportly_unassigned_filter, sirportly_waitingstaff_filter

const SIRPORTLY_ENDPOINT = process.env.SIRPORTLY_ENDPOINT || "https://support.dogsbody.com/api/v2/tickets"
const SIRPORTLY_TOKEN = process.env.SIRPORTLY_TOKEN || console.error("No SIRPORTLY_TOKEN set in environment, please set!")
const SIRPORTLY_KEY = process.env.SIRPORTLY_KEY || console.error("No SIRPORTLY_KEY set in environment, please set!")

export const SIRPORTLY_FILTERS = {
    resolved_filter: '68',
    waitingstaff_filter: '72',
    
    orange_filter: '1', // unnasigned
    red_filter: '33',
    blue_filter: '65',

    total_filter: '27', // for green

    daily_filter: '84',
}

export const SIRPORTLY_USER_FILTERS = {
    red_filter: '31',
    green_filter: '58',
    blue_filter: '30',
}



// This is used to get data for a specific filter in sirportly
// it accepts a filterID and a username/False if no user needed.
// it returns a promise that resolves to a json object
// view.pagination.total_records for the total number of records
export async function getSirportlyView(filterId: string, user?: string): Promise<any> {
    const headers = new Headers();
    SIRPORTLY_TOKEN ? headers.append('X-Auth-Token', SIRPORTLY_TOKEN) : 0
    SIRPORTLY_KEY ? headers.append('X-Auth-Secret', SIRPORTLY_KEY) : 0
    const params = new URLSearchParams({
        filter: filterId,
    })
    if (user) params.append('user', user)

    const res = await fetch(SIRPORTLY_ENDPOINT + "/filter?" + params, {
        method: "GET",
        headers
    })

    return await res.json()
}

// def get_sirportly_data():
//     """
//     Get all the data we need from sirportly and store it in a dict
//     """
//     sirportly_data = {'users': {}}
//     sirportly_data['unassigned_tickets'] = sirportly_filter(sirportly_unassigned_filter)
//     sirportly_data['waitingstaff_tickets'] = sirportly_filter(sirportly_waitingstaff_filter)
//     sirportly_data['total_tickets'] = sirportly_filter(sirportly_total_filter)
//     sirportly_data['red_tickets'] = sirportly_filter(sirportly_red_filter)
//     sirportly_data['blue_tickets'] = sirportly_filter(sirportly_blue_filter)
//     sirportly_data['resolved_tickets'] = sirportly_filter(sirportly_resolved_filter)
//     # This is close to being able to skip the red and blue filters and just
//     # add to the total as part of each user, this wouldn't account for the
//     # status of tickets in unassigned
//     # Using a sirportly report may be a more efficient way to gather the
//     # data we need but I couldn't quickly get a query working so I left it
//     for user in sirportly_users:
//         sirportly_data['users'][user] = {}
//         sirportly_data['users'][user]['red'] = sirportly_filter(sirportly_reduser_filter, user)
//         sirportly_data['users'][user]['green'] = sirportly_filter(sirportly_greenuser_filter, user)
//         sirportly_data['users'][user]['blue'] = sirportly_filter(sirportly_blueuser_filter, user)
//         sirportly_data['users'][user]['total'] = sirportly_data['users'][user]['red'] + sirportly_data['users'][user]['green'] + sirportly_data['users'][user]['blue']

//     sirportly_data['multiplier'] = sirportly_ticket_multiplier(sirportly_data)
//     sirportly_data['red_percent'] = 0
//     sirportly_data['blue_percent'] = 0
//     sirportly_data['orange_percent'] = 0
//     if sirportly_data['total_tickets']:
//         sirportly_data['red_percent'] = math.ceil(100 * sirportly_data['red_tickets'] / sirportly_data['total_tickets'])
//         sirportly_data['blue_percent'] = math.ceil(100 * sirportly_data['blue_tickets'] / sirportly_data['total_tickets'])
//         sirportly_data['orange_percent'] = math.ceil(100 * (sirportly_data['unassigned_tickets'] + sirportly_data['waitingstaff_tickets']) / sirportly_data['total_tickets'])

//     sirportly_data['green_percent'] = 100 - sirportly_data['red_percent'] - sirportly_data['orange_percent'] - sirportly_data['blue_percent']
//     return sirportly_data

// def sirportly_ticket_multiplier(sirportly_data):
//     """
//     Calculate the multiplier needed for the length of the bars on the warboard
//     """
//     ticket_counts = []
//     ticket_counts.append(sirportly_data['unassigned_tickets'])
//     ticket_counts.append(sirportly_data['waitingstaff_tickets'])
//     for user in sirportly_data['users']:
//         ticket_counts.append(sirportly_data['users'][user]['total'])

//     most_tickets = max(ticket_counts)
//     multiplier = 1
//     if most_tickets > 0:
//         multiplier = 100 / most_tickets

//     return multiplier

// def store_sirportly_results():
//     """
//     Store all the sirportly data in redis
//     """
//     sirportly_data = get_sirportly_data()
//     for key in sirportly_data:
//         if key == 'users':
//             for user in sirportly_data['users']:
//                 for key in sirportly_data['users'][user]:
//                     set_data(f'{user}_{key}', sirportly_data['users'][user][key])
//         else:
//             set_data(key, sirportly_data[key])

// def get_sirportly_results():
//     """
//     Get all the sirportly data to pass to the warboard,
//     some things need to be ints for Jinja2 to do calcs
//     """
//     sirportly_results = {'users': {}}
//     sirportly_results['unassigned_tickets'] = int(get_data('unassigned_tickets'))
//     sirportly_results['waitingstaff_tickets'] = int(get_data('waitingstaff_tickets'))
//     sirportly_results['resolved_tickets'] = int(get_data('resolved_tickets'))
//     sirportly_results['red_percent'] = get_data('red_percent')
//     sirportly_results['green_percent'] = get_data('green_percent')
//     sirportly_results['blue_percent'] = get_data('blue_percent')
//     sirportly_results['orange_percent'] = get_data('orange_percent')
//     sirportly_results['multiplier'] = float(get_data('multiplier'))
//     sirportly_results['red_tickets'] = get_data('red_tickets')
//     sirportly_results['total_tickets'] = get_data('total_tickets')
//     for user in sirportly_users:
//         sirportly_results['users'][f'{user}_red'] = int(get_data(f'{user}_red'))
//         sirportly_results['users'][f'{user}_green'] = int(get_data(f'{user}_green'))
//         sirportly_results['users'][f'{user}_blue'] = int(get_data(f'{user}_blue'))
//         sirportly_results['users'][f'{user}_total'] = get_data(f'{user}_total')

//     return sirportly_results
