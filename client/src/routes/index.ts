import type { RequestEvent } from '@sveltejs/kit';
import { saveToken } from "./calendar/2AccountToken"

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
            body: {}
        }
    }

    return {
        body: {}
    }
}