/* eslint-disable @typescript-eslint/ban-ts-comment */
// import { json } from '@sveltejs/kit';

import { client } from "$lib/server/redis";

const subscriber = client.duplicate();

subscriber.pSubscribe(
	'__keyspace@' + process.env.REDIS_DB_NUMBER + '__:*',
	async (message: string, channel: string) => {
		console.log(channel)
		// "pmessage","__key*__:*","__keyspace@0__:foo","set"

		// eslint-disable-next-line no-useless-escape
		const keyComponents =
			new RegExp(
				'^__keyspace@' +
					process.env.REDIS_DB_NUMBER +
					'__:([a-z_]+):([a-z_]+)(?:#([0-9a-z-]+))?'
			).exec(channel) || [];

		const returnDat: any = {};

		returnDat[keyComponents[1]] = {};
		switch (keyComponents[1]) {
			case 'port_monitoring':
				// console.log(message, channel)
				// .map((i: any) => {i.mod = keyComponents[2]; return i});
				returnDat[keyComponents[1]][keyComponents[2]] = JSON.parse(
					(await client.get(keyComponents[1] + ':' + keyComponents[2])) || '[]'
				)[0];
				break;
			case 'port_monitoring_success':
				// console.log(message, channel)
				returnDat[keyComponents[1]][keyComponents[2]] = JSON.parse(
					(await client.get(keyComponents[1] + ':' + keyComponents[2])) || '[]'
				)[0];
				break;
			case 'resources':
				returnDat[keyComponents[1]][keyComponents[2]] = {};
				returnDat[keyComponents[1]][keyComponents[2]][keyComponents[3]] = JSON.parse(
					(await client.get(
						keyComponents[1] + ':' + keyComponents[2] + '#' + keyComponents[3]
					)) || '[]'
				)[0];
				break;
			case 'resources_success':
				// console.log(message, channel)
				returnDat[keyComponents[1]][keyComponents[2]] = JSON.parse(
					(await client.get(keyComponents[1] + ':' + keyComponents[2])) || '[]'
				)[0];
				break;

			default:
				console.log(channel);
				return;
				break;
		}
		// console.log(returnDat)

		streamList.forEach((controller) => {
			try {
				// @ts-ignore
				controller.enqueue(JSON.stringify(returnDat) + '\n');
			} catch (error) {
				// console.log(index, error, controller)
			}
		});
		// console.log(channel, message)
	}
);

const streamList: Map<string, ReadableStreamController<unknown>> = new Map();
let streamCount = 0;


// NOTE: there is ONE UnderlyingSource for ALL the 
// ReadableStreams by default, and there is no easy 
// way to tell which stream is calling the source.
// instead, let's make a function that returns 
// a new source for each stream, so that it can be tracked.
function streamSource(): UnderlyingSource {
    let index: string;
    return {
        start(controller) {
            index = streamCount.toString();
            streamList.set(index, controller);
            streamCount++;
        },
        pull(controller) {
            // We don't really need a pull
        },
        cancel() {
            const c = streamList.get(index);
            streamList.delete(index);
            // console.log("deleted", this.index)
            try {
                c?.close();
            } catch (e) {
                // console.log(`Failed to close stream ${index}: `, e);
            }
        }
    }
	// type,
	// autoAllocateChunkSize,
};

// subscriber.pUnsubscribe("__keyspace@0__:*")
// subscriber.quit()

// let portmon_modules_checked = 0

// const portmon = (await Promise.all(
//     (await client.keys("port_monitoring:*"))
//         .map(async (mod) => {
//             portmon_modules_checked += 1
//             let ret: any[] = JSON.parse(await client.get(mod) || '')
//             let dat = ret[0].map((i: any) => {i.mod = mod; return i});
//             return dat
//         })
//     )).flat(1)
// let portmon_ag_results = {
//     up: 0,
//     down: 0,
//     paused: 0,

//     total_accounts: 0,
//     failed_accounts: 0,
// };

// (await client.keys("port_monitoring_success:*"))
//     .map(async (mod: string) => {
//         let ret: any[] = JSON.parse(await client.get(mod) || '')
//         let dat = ret[0];
//         portmon_ag_results.up += dat.up
//         portmon_ag_results.down += dat.down
//         portmon_ag_results.paused += dat.paused
//         portmon_ag_results.total_accounts += dat.total_accounts
//         // console.log(mod, dat.valid_until < Date.now())
//         if (dat.valid_until < Date.now()) {
//             portmon_ag_results.failed_accounts += dat.total_accounts
//         } else {
//             portmon_ag_results.failed_accounts += dat.failed_accounts
//         }
//     })

// let resmon_ag_results: any = {};

// (await client.keys("resources_success:*"))
//     .map(async (mod: string) => {
//         let ret: any[] = JSON.parse(await client.get(mod) || '')
//         let dat = ret[0];
//         resmon_ag_results.total_checks += dat.total_checks
//         resmon_ag_results.total_accounts += dat.total_accounts

//         if (dat.valid_until < Date.now()) {
//             resmon_ag_results.failed_accounts += dat.total_accounts
//         } else {
//             resmon_ag_results.failed_accounts += dat.failed_accounts
//         }
//     })

// const resmon = await Promise.all(
//     (await client.keys("resources:*"))
//         .map(async (mod) => {
//             let ret: any[] = JSON.parse(await client.get(mod) || '')
//             let dat = ret[0];
//             dat.key = mod
//             return dat
//         })

//     )

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	const body = new ReadableStream(streamSource(), {
		highWaterMark: 6,
		size: () => 1
	});

	// Suggestion (check for correctness before using):
	// return json(body, {
	// 	headers: {
	// 		'transfer-encoding': 'chunked'
	// 	}
	// });
	// return {
	// 	headers: {
	// 		'transfer-encoding': 'chunked'
	// 	},
	// 	// body: { portmon, resmon, portmon_ag_results, resmon_ag_results }
	// 	body: body
	// };
	return new Response(body, {
		headers: {
			'transfer-encoding': 'chunked'
		}
	})
}
