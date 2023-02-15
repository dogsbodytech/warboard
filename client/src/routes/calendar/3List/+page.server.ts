import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
// readdir, mkdir

import type { RequestEvent } from '@sveltejs/kit';

import { google } from 'googleapis';

const SCOPES = [
	'https://www.googleapis.com/auth/calendar.readonly',
	'https://www.googleapis.com/auth/userinfo.profile'
];

const id = () => {
	return Math.floor((1 + Math.random()) * 0x10000)
		.toString(16)
		.substring(1);
};

export async function load(reqe: RequestEvent) {
	// console.log(reqe.url.searchParams.get("credentials"))
	let list;

	try {
		list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' });
	} catch (error) {
		// failed to
	}

	const projectCredentialList = JSON.parse(list || '{}') as any;

	const newList: string[] = projectCredentialList?.list || [];

	const code = reqe.url.searchParams.get('credentials');

	if (newList.find((el) => code == el)) {
		const content = await fs.readFile(path.join(os.homedir(), code + '.json'), {
			encoding: 'utf8'
		});

		const credentials = JSON.parse(content);

		// console.log(credentials)

		const { client_secret, client_id, redirect_uris } = credentials.web;
		const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

		let listText;

		try {
			listText = await fs.readFile(path.join(os.homedir(), 'tokenList.json'), { encoding: 'utf8' });
		// eslint-disable-next-line no-empty
		} catch (error) {}

		const gid = reqe.url.searchParams.get('gid');

		// console.log(list)

		const accountToken = (JSON.parse(listText || '{}') as any).list.find(
			(va: any) => va.credentials == code && va.gid == gid
		);

		if (accountToken?.token) {
			try {
				oAuth2Client.setCredentials(accountToken.token);
				const calendar = google.calendar({ version: 'v3' });
				const calendarList = await calendar.calendarList.list({ auth: oAuth2Client });

				return { calendarList: calendarList.data.items, code, gid };
			} catch (error) {
				return { error };
			}
		} else {
			return { error: { code: 'E_NO_TOKEN' } };
		}
	} else {
		console.log('E bad code', code, newList);

		return { error: { code: 'CRED_CODE_INVALID' } };
	}
}
