import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
// readdir, mkdir

import type { RequestHandler, RequestEvent } from '@sveltejs/kit';

import { google } from "googleapis"

const SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/userinfo.profile'];

let id = () => {
    return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
}

export async function GET(reqe: RequestEvent) {
    // console.log(reqe.url.searchParams.get("credentials"))
    let list;

    try {
        list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' })
    } catch (error) {
    }



    let projectCredentialList = JSON.parse(list || "{}") as any

    let newList: string[] = projectCredentialList?.list || []

    const code = reqe.url.searchParams.get("credentials")

    if (newList.find((el) => code == el)) {

        const content = await fs.readFile(path.join(os.homedir(), code + '.json'), { encoding: 'utf8' })

        const credentials = JSON.parse(content)

        // console.log(credentials)

        const { client_secret, client_id, redirect_uris } = credentials.web;
        const oAuth2Client = new google.auth.OAuth2(
            client_id, client_secret, redirect_uris[0]);

        let listText;

        try {
            listText = await fs.readFile(path.join(os.homedir(), 'tokenList.json'), { encoding: 'utf8' })
        } catch (error) {
        }


        const gid = reqe.url.searchParams.get("gid")


        // console.log(list)

        let accountToken = (JSON.parse(listText || "{}") as any).list
            .find((va: any) => (va.credentials == code) && (va.gid == gid))

        let calendarId = reqe.url.searchParams.get("calid")
        
        if (accountToken.token && calendarId) {
            oAuth2Client.setCredentials(accountToken.token)
            const calendar = google.calendar({ version: 'v3' });

            let eventList = await calendar.events.list({
                calendarId,
                auth: oAuth2Client
            })

            // console.log(eventList)



            return {
                body: { calendarId, code, gid, eventList: eventList.data  }
            }
            
        } else {
            return {
                body: { error: { code: "E_NO_TOKEN" } }
            }
        }

    } else {
        console.log("E bad code", code, newList)

        return {
            body: { error: { code: "CRED_CODE_INVALID" } }
        }
    }
}
