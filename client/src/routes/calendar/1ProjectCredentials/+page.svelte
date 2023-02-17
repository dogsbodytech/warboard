<script lang=ts>
	export let data;
	let { projectCredentialList }: any = data;
</script>

<form action="?/upload" method="post" enctype="multipart/form-data">
	<input type="file" name="credentialsFile" accept="text/json" />
	<input type="submit" value="Upload" />
</form>

<ul>
	{#each projectCredentialList.list as code}
		<li>
			<a href="/calendar/2AccountToken?credentials={code}">{code}</a>
		</li>
	{/each}
</ul>
