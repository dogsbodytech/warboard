<script lang=ts>
    export let data: any;
    let { projectTokenList, authUrl }: any = data;
    
</script>
<a href="{authUrl}">new account</a>
<br>

{#each projectTokenList as account}
<a href="/calendar/3List?credentials={account.credentials}&gid={account.gid}">{account.gid} / {account.name}</a><br>
{/each}
