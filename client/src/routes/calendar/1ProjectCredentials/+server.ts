import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
// readdir, mkdir

const id = () => {
    return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
}

/** @type {import('./$types').PageServerLoad} */
export async function load() {

    let list;

    try {
        list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' })
    // eslint-disable-next-line no-empty
    } catch (error) {
    }

    const projectCredentialList = JSON.parse(list || "{}") as object


    return { projectCredentialList }
}

/** @type {import('./$types').RequestHandler} */
export async function POST({ request }: { request: any }) {
    // console.log(request)


    let list;

    try {
        list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' })
    // eslint-disable-next-line no-empty
    } catch (error) {
    }


    // console.log(list)

    const projectCredentialList = JSON.parse(list || "{}");

    const data = await request.json();

    const file = JSON.stringify(data['credentialsFile']);
    const fileID = id()

    await fs.writeFile(path.join(os.homedir(), fileID + ".json"), file, { encoding: 'utf8' });

    if (!projectCredentialList.list) projectCredentialList.list = []
    projectCredentialList.list.push(fileID)

    fs.writeFile(path.join(os.homedir(), 'credentialList.json'), JSON.stringify(projectCredentialList), { encoding: 'utf8' })

    // return validation errors

}
