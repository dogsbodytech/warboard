import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
// readdir, mkdir

import { fail, type RequestEvent } from '@sveltejs/kit';

import { google } from "googleapis"
import { getProjectCredentialList } from '$lib/server/credentialsList';

const SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/userinfo.profile'];

const id = () => {
    return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
}

export async function _saveToken(credCode: string | null, tokenCode: string) {
    // console.log(reqe.url.searchParams.get("credentials"))
    let list;

    try {
        list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' })
    // eslint-disable-next-line no-empty
    } catch (error) {
    }



    const credList = await getProjectCredentialList()

    if (credList.list.find((el) => credCode == el)) {

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

            const idToken = await oAuth2Client.verifyIdToken({ idToken: token.tokens.id_token, audience: credentials.web.client_id })
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
            const names = res?.data?.names
            if (names) {
                const namel = names[0]
                gid = namel?.metadata?.source?.id
                name = namel?.displayName
            }
        }


        let listText;

        try {
            listText = await fs.readFile(path.join(os.homedir(), 'tokenList.json'), { encoding: 'utf8' })
        // eslint-disable-next-line no-empty
        } catch (error) {
        }


        // console.log(list)

        const projectToken = JSON.parse(listText || "{}") as any


        let projectTokenList: any[] = projectToken?.list || []

        projectTokenList = projectTokenList
            .filter((va) => {
                const pred = !((va.credentials == credCode) && (va.gid == gid))
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

export async function load(reqe: RequestEvent) {
    // console.log(reqe.url.searchParams.get("credentials"))
    let list;

    try {
        list = await fs.readFile(path.join(os.homedir(), 'credentialList.json'), { encoding: 'utf8' })
    // eslint-disable-next-line no-empty
    } catch (error) {
    }



    const projectCredentialList = JSON.parse(list || "{}") as any

    const newList: string[] = projectCredentialList?.list || []

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
        // eslint-disable-next-line no-empty
        } catch (error) {
        }


        const projectToken = JSON.parse(listText || "{}") as any
        // console.log(projectToken)


        const projectTokenList: any[] = (projectToken?.list || [])
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

        return { projectTokenList, authUrl }
    } else {
        console.log("E bad code", code, newList)

        return fail(400, { error: { code: "CRED_CODE_INVALID" } })
    }
}
