<script lang=ts>

    export let data;
    let { projectCredentialList }: any = data;

    let fileInput: HTMLInputElement;
    let files: FileList|null|undefined;

    // function getBase64(file: Blob) {
    //     const reader = new FileReader();
    //     reader.readAsDataURL(file);
    //     reader.addEventListener("load", e => {
    //         uploadFunction(e?.target?.result);
    //     });
    // };


    function getJson(file: Blob) {
        const reader = new FileReader();
        reader.readAsText(file);
        reader.addEventListener("load", e => {
            // @ts-ignore
            let str: string = e?.target?.result || ""

            uploadFunction(JSON.parse(str));
        });
    };

    async function uploadFunction(result: any) {
        const data: any = {}
        data.credentialsFile = result;
        console.log(data);
        await fetch(`/calendar/1ProjectCredentials`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json'
            },
            body: JSON.stringify(data)
        });
    };


</script>

<div class="container">
    <input class="hidden" id="file-to-upload" type="file" accept=".json" bind:files bind:this={fileInput} on:change={() => {if (files) return getJson(files[0])}}/>
    <button class="upload-btn" on:click={ () => fileInput.click() }>Upload</button>
</div>

{JSON.stringify(projectCredentialList)}
{#each projectCredentialList.list as code}
<a href="/calendar/2AccountToken?credentials={code}">{code}</a><br>
{/each}
