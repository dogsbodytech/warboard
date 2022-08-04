<script lang=ts>
    import "$lib/groupBy"
	// data: {
	//     kind: 'calendar#events',
	//     etag: '"..."',
	//     summary: 'Holidays in United Kingdom',
	//     updated: '2022-08-03T00:55:25.000Z',
	//     timeZone: 'Europe/London',
	//     accessRole: 'reader',
	//     defaultReminders: [],
	//     nextSyncToken: '...',
	//     items: [
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object], [Object], [Object], [Object],
	//       [Object], [Object]
	//     ]
	//   },

    // {
    // "kind": "calendar#event",
    // "etag": "\"....\"",
    // "id": "20210104_ijt8aj9bdcrvi9l2d25vgcvs44",
    // "status": "confirmed",
    // "htmlLink": "https://www.google.com/calendar/event?eid=MjAyMTAxMDRfaWp0OGFqOWJkY3J2aTlsMmQyNXZnY3ZzNDQgZW4udWsjaG9saWRheUB2",
    // "created": "2021-08-26T11:27:05.000Z",
    // "updated": "2021-08-26T11:27:05.030Z",
    // "summary": "2nd January (substitute day) (Scotland)",
    // "description": "Public holiday in Scotland",
    // "creator": {// @ts-ignore
    //     "email": "en.uk#holiday@group.v.calendar.google.com",
    //     "displayName": "Holidays in United Kingdom",
    //     "self": true
    // },
    // "organizer": {
    //     "email": "en.uk#holiday@group.v.calendar.google.com",
    //     "displayName": "Holidays in United Kingdom",
    //     "self": true
    // },
    // "start": {
    //     "date": "2021-01-04"
    // },
    // "end": {
    //     "date": "2021-01-05"
    // },
    // "transparency": "transparent",
    // "visibility": "publ// @ts-ignorelt"
    // }
	export let eventList: any;
    $: eventCalList = eventList.items as any[]

    $: calendar = Object.entries(eventCalList
        .map((item, ind) => {
            if (item.start.dateTime) {
                let datetime = new Date(item.start.dateTime)
                item.start.date = datetime.toISOString().split("T")[0]
                let endDatetime = new Date(item.end.dateTime)
                item.end.date = endDatetime.toISOString().split("T")[0]
                try {
                    let currentSummary = item.summary
                    item.summary = `${datetime.toTimeString().slice(0, 5)} - ${endDatetime.toTimeString().slice(0, 5)}: ` + currentSummary
                } catch (e) {}
            }
            if (item.start.date == item.end.date) {
                item.date = item.start.date
                return [item]
            } else {
                let itArray = []
                for (var d = new Date(item.start.date); d <= new Date(new Date(item.end.date).getTime()-1000); d.setDate(d.getDate() + 1)) {
                    let newItem: any = {}
                    Object.assign(newItem, item)
                    newItem.date = new Date(d).toISOString().split("T")[0];
                    itArray.push(newItem);
                }
                return itArray
            }

        })
        .flat(1)
        // @ts-ignore
        .groupBy((el) => el.date))
        .sort((a, b) => a[0].localeCompare(b[0])) as [string, any[]][]
    
</script>
<h1>{eventList.summary}</h1>
{#each calendar as [ date, events]}
{@const dateString = new Date(date).toDateString()}
<h2>{dateString}</h2>
<ul>
{#each (events) as event}
<li>{event.summary}: {event.description}</li>
{/each}
</ul>
{/each}