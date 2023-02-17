import { getCalendarConfig } from "$lib/server/calendarConfig";
import { getSirportlyView, SIRPORTLY_FILTERS } from "$lib/server/sirportly";



/** @type {import('./$types').PageServerLoad} */
export async function load() {
    const filters = await Promise.all(Object.entries(SIRPORTLY_FILTERS).map(async (v) => {
        return [ v[0], await getSirportlyView(v[1]) ]
    }))
    const calendarConfig = await getCalendarConfig()
    
    return { data: { filters }, calendarConfig }
}