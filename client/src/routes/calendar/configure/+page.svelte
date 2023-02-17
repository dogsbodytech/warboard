<script lang=ts>
	import type { CalendarConfig } from "$lib/calendarConfigTypes";


	export let data;
	let { calendarConfig }: { calendarConfig: CalendarConfig[] } = data;
</script>

<form action="?/upload" method="post" enctype="multipart/form-data">
	<p>Upload new config JSON file:</p>
	<input type="file" name="configFile" accept="text/json" />
	<input type="submit" value="Upload" />
</form>

<ol>
	{#each calendarConfig as calendar}
		<li>
			<p>title: {calendar.title}</p>
			<p>subcalendars: </p>
			<ul>
				{#each calendar.calendars as subcal}
					<li><pre>{JSON.stringify(subcal)}</pre></li>
				{/each}
			</ul>
		</li>
	{/each}
</ol>
