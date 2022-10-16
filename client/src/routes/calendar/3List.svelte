<script lang=ts>
	export let calendarList: any;
	export let code: any;
	export let gid: any;
</script>

{#each calendarList as calendar}
<a href="/calendar/4Calendar?credentials={code}&gid={gid}&calid={encodeURIComponent(calendar.id)}">{calendar.summary}: {calendar.description}</a><br />
{/each}
