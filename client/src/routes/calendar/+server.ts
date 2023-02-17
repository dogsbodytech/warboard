import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
// readdir, mkdir

import { fail, json, type RequestEvent } from '@sveltejs/kit';

import { google } from "googleapis"
import { getProjectCredentialList } from '$lib/server/credentialsList';


export async function GET({ url }: {url: URL}) {
    // console.log(url.searchParams.get("credentials"))

    const credList = await getProjectCredentialList();

    const code = url.searchParams.get("credentials")
    const gid = url.searchParams.get("gid")
    const calendarId = url.searchParams.get("calid")

    if (credList.list.find((el) => code == el)) {

        const content = await fs.readFile(path.join(os.homedir(), code + '.json'), { encoding: 'utf8' })

        const credentials = JSON.parse(content)

        // console.log(credentials)

        const { client_secret, client_id, redirect_uris } = credentials.web;
        const oAuth2Client = new google.auth.OAuth2(
            client_id, client_secret, redirect_uris[0]);

        let listText;

        try {
            listText = await fs.readFile(path.join(os.homedir(), 'tokenList.json'), { encoding: 'utf8' })
        // eslint-disable-next-line no-empty
        } catch (error) {
        }




        // console.log(list)

        const accountToken = (JSON.parse(listText || "{}") as any).list
            .find((va: any) => (va.credentials == code) && (va.gid == gid))

        
        if (accountToken.token && calendarId) {
            oAuth2Client.setCredentials(accountToken.token)
            const calendar = google.calendar({ version: 'v3' });

            const eventList = await calendar.events.list({
                calendarId,
                auth: oAuth2Client
            })

            // console.log(eventList)



            return json({ calendarId, code, gid, eventList: eventList.data  })
            
		} else {
			return fail(400, { error: { code: "E_NO_TOKEN" } })
		}
	} else {
		console.log('E bad code', code, credList.list);

        return fail(400, { error: { code: "CRED_CODE_INVALID" } })
	}
}
