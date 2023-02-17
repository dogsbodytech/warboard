import { getProjectCredentialList, saveProjectCredentialList } from '$lib/server/credentialsList';
import { fail, type Actions } from '@sveltejs/kit';
// readdir, mkdir

import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

const id = () => {
    return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
}

/** @type {import('./$types').PageServerLoad} */
export async function load() {

    const credList = await getProjectCredentialList()


    return { projectCredentialList: credList }
}

export const actions: Actions = {
  upload: async ({ request }) => {
    const form = await request.formData();

    const data = form.get('credentialsFile');

    if (!data) {
      return fail(400, { message: 'No file provided!' });
    }


    const file: File = data.valueOf() as File;


    const fileID = id()

    console.log(fileID, file)


    await fs.writeFile(path.join(os.homedir(), fileID + ".json"), file.stream(), { encoding: 'utf8' });

    // Append credential file to credential list

    const credList = await getProjectCredentialList()

    credList.list.push(fileID)

    saveProjectCredentialList(credList)

    return { success: true };
  }
};
