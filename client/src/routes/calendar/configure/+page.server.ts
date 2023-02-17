import { getCalendarConfig, saveCalendarConfig } from '$lib/server/calendarConfig';
import { fail, type Actions } from '@sveltejs/kit';
// readdir, mkdir

import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

/** @type {import('./$types').PageServerLoad} */
export async function load() {

    const calendarConfig = await getCalendarConfig()


    return { calendarConfig }
}

export const actions: Actions = {
  upload: async ({ request }) => {
    const form = await request.formData();

    const data = form.get('configFile');

    if (!data) {
      return fail(400, { message: 'No file provided!' });
    }


    const file: File = data.valueOf() as File;

    const fileData = JSON.parse(await file.text())

    await saveCalendarConfig(fileData)

    return { success: true };
  }
};
