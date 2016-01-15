import redis
from config import redis_host, redis_port, redis_db

def redis_connect():
    rcon = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
    # All redis connection errors will be logged when getting/setting as when setting rcon you will never receive an Exception
    # unless the redis module isn't installed.
    return(rcon)
