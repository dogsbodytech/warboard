/* eslint-disable @typescript-eslint/no-explicit-any */
import { client } from "$lib/server/redis";

const keyRegex = /^([a-z_]+):([a-z_]+)(?:#([0-9a-z-]+))?/

// import type { RequestEvent } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load() {

    const port_monitoring: any = {};
    const port_monitoring_success: any = {};
    const resources: any = {};
    const resources_success: any = {};

    (await client.keys("port_monitoring:*"))
        .forEach(async (mod) => {
            const segs = keyRegex.exec(mod) || []
            const ret: any[] = JSON.parse(await client.get(mod) || '')[0]
            port_monitoring[segs[2]] = ret
        });

    (await client.keys("port_monitoring_success:*"))
        .forEach(async (mod) => {
            const segs = keyRegex.exec(mod) || []
            const ret: any[] = JSON.parse(await client.get(mod) || '')[0]
            port_monitoring_success[segs[2]] = ret
        });

    (await client.keys("resources:*"))
        .forEach(async (mod) => {
            const segs = keyRegex.exec(mod) || []
            const ret: any[] = JSON.parse(await client.get(mod) || '')[0]
            if (typeof resources[segs[2]] === "undefined")
                resources[segs[2]] = {}
            resources[segs[2]][segs[3]] = ret
        });

    (await client.keys("resources_success:*"))
        .forEach(async (mod) => {
            const segs = keyRegex.exec(mod) || []
            const ret: any[] = JSON.parse(await client.get(mod) || '')[0]
            resources_success[segs[2]] = ret
        });


    return { data: { port_monitoring, port_monitoring_success, resources, resources_success } }
}