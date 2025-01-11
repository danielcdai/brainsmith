import json
import redis
from cortex.config import settings


redis_client = redis.StrictRedis(host=settings.redis_host, port=settings.redis_port, db=0)


def update_task(task_id, task_info):
    """
    Save the task information to Redis.
    """
    redis_client.set(task_id, json.dumps(task_info))


def load_all_tasks():
    """
    Load all the tasks from Redis.
    """
    tasks = {}
    for key in redis_client.keys():
        task_info = redis_client.get(key)
        tasks[key] = json.loads(task_info)
    return tasks


def load_task_by_id(task_id):
    """
    Load the task information from Redis by task_id.
    """
    task_info = redis_client.get(task_id)
    if task_info is None:
        return None
    return json.loads(task_info)