import redis
from config import redis_host, redis_port, redis_db
import logging
logger = logging.getLogger(__name__)

def redis_connect():
    rcon = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
    # All redis connection errors will be logged when getting/setting as when setting redis_connect() you will never receive an Exception
    # unless the redis module isn't installed.
    return(rcon)

def set_data(key, value): # Used to set keys in redis
    try:
        redis_connect().set(key, value)
    except redis.exceptions.ConnectionError:
        logger.error('Could not set '+key+' in Redis')

def set_volatile_data(key, value, ttl_seconds):
    """
    Sets key, value in redis with a given time to live
    """
    try:
        conn = redis_connect()
        conn.set(key, value)
        conn.expire(key, ttl_seconds)
    except redis.exceptions.ConnectionError:
        logger.error('Could not set '+key+' in Redis')

def get_data(key): # Used to get keys from redis
    try:
        value = redis_connect().get(key)
    except redis.exceptions.ConnectionError:
        logger.error('Could not get '+key+' from Redis')
        return(None)
    return(value)

def get_all_data(key): # Used to get all keys with a pattern e.g pingdom_*
    try:
        value = redis_connect().keys(key)
    except redis.exceptions.ConnectionError:
        logger.error('Could not get '+key+' from Redis')
        return(None)
    return(value)

def delete_data(key): # Used to delete keys
    try:
        redis_connect().delete(key)
    except redis.exceptions.ConnectionError:
        logger.error('Could delete '+key+' in Redis')
