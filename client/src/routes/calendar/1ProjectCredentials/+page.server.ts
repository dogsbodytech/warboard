import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
// readdir, mkdir

let id = () => {
    return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
}

/** @type {import('./__types/items').RequestHandler} */
export async function GET() {

    let list;

    try {
        list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' })
    } catch (error) {
    }

    let projectCredentialList = JSON.parse(list || "{}") as object


    return {
        body: { projectCredentialList }
    }
}

/** @type {import('./__types/items').RequestHandler} */
export async function POST({ request }: { request: any }) {
    // console.log(request)


    let list;

    try {
        list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' })
    } catch (error) {
    }


    // console.log(list)

    let projectCredentialList = JSON.parse(list || "{}") as any

    const data = JSON.parse((await request.text()).toString());

    const file = JSON.stringify(data['credentialsFile']);
    let fileID = id()

    await fs.writeFile(path.join(os.homedir(), fileID + ".json"), file, { encoding: 'utf8' });

    if (!projectCredentialList.list) projectCredentialList.list = []
    projectCredentialList.list.push(fileID)

    fs.writeFile(path.join(os.homedir(), 'credentialList.json'), JSON.stringify(projectCredentialList), { encoding: 'utf8' })

    // return validation errors
    return {
        status: 200,
        body: { sucess: true }
    };

}
