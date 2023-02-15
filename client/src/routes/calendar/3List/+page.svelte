<script lang=ts>
	export let data: any;

	export let { calendarList, code, gid }: any = data;
</script>

{#each calendarList as calendar}
<a href="/calendar/4Calendar?credentials={code}&gid={gid}&calid={encodeURIComponent(calendar.id)}">{calendar.summary}: {calendar.description}</a><br />
{/each}
