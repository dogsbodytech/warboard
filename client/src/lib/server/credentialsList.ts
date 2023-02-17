import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

export async function getProjectCredentialList(): Promise<{ list: string[] }> {
	let list;

	try {
		list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' });
		// eslint-disable-next-line no-empty
	} catch (error) {}
	const projectCredentialList = JSON.parse(list || '{}');
	if (!projectCredentialList?.list) projectCredentialList.list = [];

    // console.log(projectCredentialList)
	return projectCredentialList;
}

export async function saveProjectCredentialList(data: { list: string[] }) {
	await fs.writeFile(path.join(os.homedir(), 'credentialList.json'), JSON.stringify(data), {
		encoding: 'utf8'
	});
}
