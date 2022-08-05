import { createClient } from 'redis';
import { saveToken } from "./calendar/2AccountToken"

const client = createClient()
await client.connect()

import type { RequestEvent } from '@sveltejs/kit';

/** @type {import('./__types/items').RequestHandler} */
export async function GET(reqe: RequestEvent) {
    let code = reqe.url.searchParams.get("code")
    if (code) {

        await saveToken(reqe.url.searchParams.get("state"), code)
        // await saveToken(code)
        return {
            status: 303,
            headers: {
              location: `/calendar/2AccountToken?credentials=` + reqe.url.searchParams.get("state")
            },
            body: {  }
        }
    }

    let port_monitoring: any = {};
    let port_monitoring_success: any = {};
    let resources: any = {};
    let resources_success: any = {};

    (await client.keys("port_monitoring:*"))
        .forEach(async (mod) => {
            let segs = /^([a-z_]+):([a-z_]+)(?:#([0-9a-z\-]+))?/.exec(mod) || []
            let ret: any[] = JSON.parse(await client.get(mod) || '')[0]
            port_monitoring[segs[2]] = ret
        });

    (await client.keys("port_monitoring_success:*"))
        .forEach(async (mod) => {
            let segs = /^([a-z_]+):([a-z_]+)(?:#([0-9a-z\-]+))?/.exec(mod) || []
            let ret: any[] = JSON.parse(await client.get(mod) || '')[0]
            port_monitoring_success[segs[2]] = ret
        });

    (await client.keys("resources:*"))
        .forEach(async (mod) => {
            let segs = /^([a-z_]+):([a-z_]+)(?:#([0-9a-z\-]+))?/.exec(mod) || []
            let ret: any[] = JSON.parse(await client.get(mod) || '')[0]
            if (typeof resources[segs[2]] === "undefined")
                resources[segs[2]] = {}
            resources[segs[2]][segs[3]] = ret
        });

    (await client.keys("resources_success:*"))
        .forEach(async (mod) => {
            let segs = /^([a-z_]+):([a-z_]+)(?:#([0-9a-z\-]+))?/.exec(mod) || []
            let ret: any[] = JSON.parse(await client.get(mod) || '')[0]
            resources_success[segs[2]] = ret
        });


    return {

        body: { data: { port_monitoring, port_monitoring_success, resources, resources_success } }
    }
}