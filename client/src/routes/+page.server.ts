import type { RequestEvent } from '@sveltejs/kit';
import { _saveToken } from "./calendar/2AccountToken/+page.server"
import { redirect } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load(reqe: RequestEvent) {
    const code = reqe.url.searchParams.get("code")
    if (code) {
        await _saveToken(reqe.url.searchParams.get("state"), code)
        // await saveToken(code)
        throw redirect(303, `/calendar/2AccountToken?credentials=` + reqe.url.searchParams.get("state"))
    }

    return {}
}