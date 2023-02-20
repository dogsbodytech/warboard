<script lang="ts">
	import '$lib/groupBy';
	import todayDate from './todayDate';
	import xss from "xss"
	import type { ExternalCalendar } from './calendarConfigTypes';
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
	// "visibility": "public"
	// }

	export let calTitle: string | undefined;
	export let calendars: ExternalCalendar[];
	export let asc = false;
	// export let filterAfter = todayDate()

	let calDefaultTitle = 'Calendar';

	async function pipeline(calendars: ExternalCalendar[]) {
		let eventLists = await Promise.all(
			calendars.map(async (calendar) => {
				let params = new URLSearchParams({
					credentials: calendar.credentials,
					gid: calendar.gid,
					calid: calendar.calendarId
				});
				let res = await fetch('/calendar?' + params);
				let json = await res.json();
				if (!calendar.showDescription) {
				json.eventList.items.map((event: any) => {
					event.description = undefined
					event
				})
				}
				return json
			})
		);
		if (eventLists[0]?.eventList?.summary) {
			calDefaultTitle = eventLists[0].eventList.summary;
		}
		let mergedItemList = eventLists
			.map((list) => list.eventList.items).flat(1)


		return Object.entries(
			mergedItemList
				.map((item) => {
					if (item.start.dateTime) {
						let datetime = new Date(item.start.dateTime);
						item.start.date = datetime.toISOString().split('T')[0];
						let endDatetime = new Date(item.end.dateTime || item.start.dateTime);
						item.end.date = endDatetime.toISOString().split('T')[0];
						try {
							let currentSummary = item.summary;
							item.summary =
								`${datetime.toTimeString().slice(0, 5)} - ${endDatetime
									.toTimeString()
									.slice(0, 5)}: ` + currentSummary;
						} catch (e) {}
					}
					if (item.start.date == item.end.date) {
						item.date = new Date(item.start.date).toISOString().split('T')[0];
						return [item];
					} else {
						let itArray = [];
						for (
							var d = new Date(item.start.date);
							d <= new Date(new Date(item.end.date).getTime() - 1000);
							d.setDate(d.getDate() + 1)
						) {
							let newItem: any = {};
							Object.assign(newItem, item);
							newItem.date = new Date(d).toISOString().split('T')[0];
							itArray.push(newItem);
						}
						return itArray;
					}
				})
				// .filter((v) => {
				// 	let a = new Date(v?.end?.dateTime || v?.end?.date)
				// 	let b = filterAfter
				// 	console.log(v, a, b, a > b)
				// 	return a > b
				// })
				.flat(1)
				.sort((a, b) => {
					let aDate = new Date(a?.start?.dateTime || a?.start?.date);
					let bDate = new Date(b?.start?.dateTime || b?.start?.date);
					if (!asc) {
						return aDate - bDate
					} else {
						return bDate - aDate
					}
				})
				// @ts-ignore
				.groupBy((el) => el.date)
		).sort((a, b) => asc ? -a[0].localeCompare(b[0]) : a[0].localeCompare(b[0])) as [string, any[]][];
	}

	$: calendarPromise = pipeline(calendars);
</script>

<h1>{calTitle || calDefaultTitle}</h1>
{#await calendarPromise}
	<p>...waiting</p>
{:then calendar}
{#each calendar as [date, events]}
	{@const dateString = new Date(date).toDateString()}
	<h2>{dateString}</h2>
	<ul>
		{#each events as event}
			<li>
				{#if event.description}
					<a class="summary" href={event.htmlLink}>{event.summary}</a>:
					<p class="description">
						{@html xss(event.description)}
					</p>
                    {:else}
					<a class="summary" href={event.htmlLink}>{event.summary}</a>
				{/if}
			</li>
		{/each}
	</ul>
{/each}
{:catch error}
	<p style="color: red">{error.message}</p>
{/await}

<style>
	ul {
		border: 1px solid gray;
		border-radius: 10px;
		padding: 0;
		background: aliceblue;
		list-style: none;
	}

	li {
		padding: 1em;
	}

	li:not(:first-child) {
		border-top: 1px solid gray;
		/* margin-top: 1em; */
	}

	a {
		color: inherit;
	}

	p.description {
		margin: 0.75em 0 0;
		white-space: pre-wrap;
	}
</style>
