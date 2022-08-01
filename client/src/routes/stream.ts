import { createClient } from 'redis';

const client = createClient()
await client.connect()

client.on('error', (err) => console.log('Redis Client Error', err));


const subscriber = client.duplicate();
await subscriber.connect()

subscriber.pSubscribe("__keyspace@0__:*", async (message: any, channel: string) => {
    // "pmessage","__key*__:*","__keyspace@0__:foo","set"
    let keyComponents = /^__keyspace@0__:([a-z_]+):([a-z_]+)(?:#([0-9a-z\-]+))?/.exec(channel) || []

    let returnDat: any = {};

    returnDat[keyComponents[1]] = {}
    switch (keyComponents[1]) {
        case "port_monitoring":
            console.log(message, channel)
            // .map((i: any) => {i.mod = keyComponents[2]; return i});
            returnDat[keyComponents[1]][keyComponents[2]] =
                JSON.parse(await client.get(keyComponents[1] + ":" + keyComponents[2]) || '[]')[0]
            break;
        case "port_monitoring_success":
            returnDat[keyComponents[1]][keyComponents[2]] =
                JSON.parse(await client.get(keyComponents[1] + ":" + keyComponents[2]) || '[]')[0]
            break
        case "resources":
            returnDat[keyComponents[1]][keyComponents[2]] = {}
            returnDat[keyComponents[1]][keyComponents[2]][keyComponents[3]] =
                JSON.parse(await client.get(keyComponents[1] + ":" + keyComponents[2] + "#" + keyComponents[3]) || '[]')[0]
            break
        case "resources_success":
            returnDat[keyComponents[1]][keyComponents[2]] =
                JSON.parse(await client.get(keyComponents[1] + ":" + keyComponents[2]) || '[]')[0]
            break

        default:
            console.log(channel)
            break;
    }

    streamList.forEach((controller, index) => {
        try {
            controller.enqueue(JSON.stringify(returnDat) + '\n')
        } catch (error) {
            console.log(index, error, controller)
        }
    })
    // console.log(channel, message)
})

let streamList: Map<string, ReadableStreamController<any>> = new Map()
let streamCount = 0;

interface RedisStreamSource extends UnderlyingSource {
    index: any;
}


const streamSource: RedisStreamSource = {
    index: 0,
    start(controller) {
        streamList.set("" + streamCount, controller)
        this.index = streamCount;
        streamCount++
    },
    pull(controller) {
        // We don't really need a pull 
    },
    cancel() {
        let c = streamList.get("" + this.index)
        streamList.delete("" + this.index)
        console.log("deleted", this.index)
        c?.close()
    },
    // type,
    // autoAllocateChunkSize,
}

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




export async function GET() {
    let body = new ReadableStream(streamSource, {
        highWaterMark: 6,
        size: () => 1,
    });

    return {
        headers: {
            'transfer-encoding': 'chunked'
        },
        // body: { portmon, resmon, portmon_ag_results, resmon_ag_results }
        body: body
    }
}