<script type="ts">
	export let portmon: any[];
	export let resmon: any[];
	console.log(portmon);
	console.log(resmon);
</script>

<!-- {#each portmon as table} -->
<table>
	{#each portmon as item}
		<tr>
			{#each Object.keys(item) as key}
				<td>{JSON.stringify(key)}: {JSON.stringify(item[key])}</td>
			{/each}
		</tr>
	{/each}
</table>
<!-- {/each} -->
<table>
	{#each resmon as item}
		<tr>
			{#each Object.keys(item) as key}
				<td>{JSON.stringify(key)}: {JSON.stringify(item[key])}</td>
			{/each}
		</tr>
	{/each}
</table>

<style>
	table,
	td {
		border: 1px solid;
	}
</style>
