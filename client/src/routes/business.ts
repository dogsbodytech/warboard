import { getSirportlyView, SIRPORTLY_FILTERS } from "$lib/sirportly";


import type { RequestEvent } from '@sveltejs/kit';

/** @type {import('./__types/items').RequestHandler} */
export async function GET(reqe: RequestEvent) {
    const filters = await Promise.all(Object.entries(SIRPORTLY_FILTERS).map(async (v, i) => {
        return [ v[0], await getSirportlyView(v[1]) ]
    }))
    
    return {

        body: { data: { filters } }
    }
}