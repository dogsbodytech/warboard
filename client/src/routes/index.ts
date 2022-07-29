import { createClient } from 'redis';

const client = createClient()
await client.connect()

client.on('error', (err) => console.log('Redis Client Error', err));




export async function GET() {
    let portmon_modules_checked = 0

    const portmon = (await Promise.all(
        (await client.keys("port_monitoring:*"))
            .map(async (mod) => { 
                portmon_modules_checked += 1
                let ret: any[] = JSON.parse(await client.get(mod) || '')
                let dat = ret[0].map((i: any) => {i.mod = mod; return i});
                return dat
            })
        )).flat(1)
    let portmon_ag_results = {
        up: 0,
        down: 0,
        paused: 0,

        total_accounts: 0, 
        failed_accounts: 0,
    };

    (await client.keys("port_monitoring_success:*"))
        .map(async (mod: string) => { 
            let ret: any[] = JSON.parse(await client.get(mod) || '')
            let dat = ret[0];
            portmon_ag_results.up += dat.up
            portmon_ag_results.down += dat.down
            portmon_ag_results.paused += dat.paused
            portmon_ag_results.total_accounts += dat.total_accounts
            // console.log(mod, dat.valid_until < Date.now())
            if (dat.valid_until < Date.now()) {
                portmon_ag_results.failed_accounts += dat.total_accounts
            } else {
                portmon_ag_results.failed_accounts += dat.failed_accounts
            }
        })
    
    let resmon_ag_results: any = {};

    (await client.keys("resources_success:*"))
        .map(async (mod: string) => { 
            let ret: any[] = JSON.parse(await client.get(mod) || '')
            let dat = ret[0];
            resmon_ag_results.total_checks += dat.total_checks
            resmon_ag_results.total_accounts += dat.total_accounts
            
            if (dat.valid_until < Date.now()) {
                resmon_ag_results.failed_accounts += dat.total_accounts
            } else {
                resmon_ag_results.failed_accounts += dat.failed_accounts
            }
        })

    const resmon = await Promise.all(
        (await client.keys("resources:*"))
            .map(async (mod) => { 
                let ret: any[] = JSON.parse(await client.get(mod) || '')
                let dat = ret[0];
                dat.key = mod
                return dat
            })
            
        )

    return {
        body: { portmon, resmon, portmon_ag_results, resmon_ag_results }
    };
}