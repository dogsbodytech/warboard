<script lang="ts">
	import { page } from "$app/stores";
	import Calendar from "$lib/Calendar.svelte";

    $: credentials = $page.url.searchParams.get("credentials")
    $: gid = $page.url.searchParams.get("gid")
    $: calendarId = $page.url.searchParams.get("calid")

</script>
<pre>{JSON.stringify({credentials, gid, calendarId})}</pre>
{#if credentials && gid && calendarId}
    <Calendar calTitle={undefined} calendars={[{credentials, gid, calendarId}]}></Calendar>
{/if}