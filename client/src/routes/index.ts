import { createClient } from 'redis';

const client = createClient()
await client.connect()

client.on('error', (err) => console.log('Redis Client Error', err));




export async function GET() {
    const portmon = (await Promise.all(
        (await client.keys("port_monitoring:*"))
            .map(async (mod) => { 
                let ret: any[] = JSON.parse(await client.get(mod) || '')
                let dat = ret[0].map((i: any) => {i.mod = mod; return i});
                return dat
            })
            
        )).flat(1)
    
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
        body: { portmon, resmon }
    };
}