import type { CalendarConfig } from '../calendarConfigTypes';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
const fileName = 'calendarConfig.json';

export async function getCalendarConfig(): Promise<CalendarConfig[]> {
	let list;

	try {
		list = await fs.readFile(path.join(os.homedir(), fileName), { encoding: 'utf8' });
		// eslint-disable-next-line no-empty
	} catch (error) {}
	const cfg = JSON.parse(list || '[]');
	return cfg;
}

export async function saveCalendarConfig(cfg: CalendarConfig[]) {
	await fs.writeFile(path.join(os.homedir(), fileName), JSON.stringify(cfg), {
		encoding: 'utf8'
	});
}
