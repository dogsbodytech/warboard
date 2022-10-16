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

export async function saveToken(credCode: string | null, tokenCode: string) {
    // console.log(reqe.url.searchParams.get("credentials"))
    let list;

    try {
        list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' })
    } catch (error) {
    }



    let projectCredentialList = JSON.parse(list || "{}") as any

    let newList: string[] = projectCredentialList?.list || []


    if (newList.find((el) => credCode == el)) {

        const content = await fs.readFile(path.join(os.homedir(), credCode + '.json'), { encoding: 'utf8' })

        const credentials = JSON.parse(content)

        // console.log(credentials)

        const { client_secret, client_id, redirect_uris } = credentials.web;
        const oAuth2Client = new google.auth.OAuth2(
            client_id, client_secret, redirect_uris[0]);


        const token = await oAuth2Client.getToken(tokenCode);
        oAuth2Client.setCredentials(token.tokens);

        let gid: string | undefined, name;

        if (token.tokens.id_token) {

            let idToken = await oAuth2Client.verifyIdToken({ idToken: token.tokens.id_token, audience: credentials.web.client_id })
            // console.log("idToken", idToken)
            gid = idToken.getPayload()?.sub
            name = idToken.getPayload()?.name

        } else {
            // console.log("no id token")

            const res = await google.people("v1").people.get({
                resourceName: 'people/me',
                personFields: 'names',
                auth: oAuth2Client
            })
            // console.log("me", res)
            let names = res?.data?.names
            if (names) {
                let namel = names[0]
                gid = namel?.metadata?.source?.id
                name = namel?.displayName
            }
        }


        let listText;

        try {
            listText = await fs.readFile(path.join(os.homedir(), 'tokenList.json'), { encoding: 'utf8' })
        } catch (error) {
        }


        // console.log(list)

        let projectToken = JSON.parse(listText || "{}") as any


        let projectTokenList: any[] = projectToken?.list || []

        projectTokenList = projectTokenList
            .filter((va) => {
                let pred = !((va.credentials == credCode) && (va.gid == gid))
                // console.log(pred)
                return pred
            })
        projectTokenList.push({ name, gid, credentials: credCode, token: token.tokens })

        // console.logoogle.calendar({ version: 'v3', auth: oAuth2Client }) = ""//
        // let fileID = id()

        // await fs.writeFile(path.join(os.homedir(), fileID + ".json"), file, { encoding: 'utf8' });
        // reqe.url.searchParams.get("code")
        // if (!projectTokenList.list) projectTokenList.list = []
        // projectTokenList.list.push(fileID)

        projectToken.list = projectTokenList
        fs.writeFile(path.join(os.homedir(), 'tokenList.json'), JSON.stringify(projectToken), { encoding: 'utf8' })

    }
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


        // console.log(list)

        let projectTokenList = (JSON.parse(listText || "{}") as any).list
            .filter((ev: any) => ev.credentials == code)
            .map((ev: any) => { return { name: ev.name, gid: ev.gid, credentials: ev.credentials } })

        // const data = JSON.parse((await reqe.request.text()).toString());

        // const file = ""//
        // let fileID = id()

        // await fs.writeFile(path.join(os.homedir(), fileID + ".json"), file, { encoding: 'utf8' });
        // reqe.url.searchParams.get("code")
        // if (!projectTokenList.list) projectTokenList.list = []
        // projectTokenList.list.push(fileID)

        // fs.writeFile(path.join(os.homedir(), 'tokenList.json'), JSON.stringify(projectTokenList), { encoding: 'utf8' })


        const authUrl = oAuth2Client.generateAuthUrl({
            access_type: 'offline',
            scope: SCOPES,
            state: code || undefined,
            prompt: "consent"
        });

        return {
            body: { projectTokenList, authUrl }
        }
    } else {
        console.log("E bad code", code, newList)

        return {
            body: { error: { code: "CRED_CODE_INVALID" } }
        }
    }
}
