import { createClient } from 'redis';

const client = createClient()
client.on('error', (err) => console.log('Redis Client Error', err));
client.connect() // await
client.select(parseInt(process.env.REDIS_DB_NUMBER || "0"))

export { client }