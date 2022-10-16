<script lang=ts>
    export let projectTokenList: any;
    export let authUrl: any;
    
</script>
<a href="{authUrl}">new account</a>
<br>

{#each projectTokenList as account}
<a href="/calendar/3List?credentials={account.credentials}&gid={account.gid}">{account.gid} / {account.name}</a><br>
{/each}
