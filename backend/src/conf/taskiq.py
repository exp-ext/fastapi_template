import asyncio
import os
from cli import AsyncDatabaseManager
from src.conf.redis import set_async_redis_client
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend, RedisScheduleSource

from . import settings

if os.getenv("TASKIQ_PROCESS") == "1":
    loop = asyncio.get_event_loop()
    loop.create_task(set_async_redis_client())

REDIS_URL = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
AMQP_URL = f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}"

result_backend = RedisAsyncResultBackend(REDIS_URL)
taskiq_broker = AioPikaBroker(AMQP_URL).with_result_backend(result_backend)

redis_source = RedisScheduleSource(
    url=REDIS_URL,
    prefix="schedule",
    buffer_size=50,
    max_connection_pool_size=100
)

scheduler = TaskiqScheduler(
    broker=taskiq_broker,
    sources=(redis_source, LabelScheduleSource(taskiq_broker)),
)


@taskiq_broker.task(schedule=[{"cron": "0 5 * * *"}])
async def dump_db():
    db_manager = AsyncDatabaseManager()
    await db_manager.dump_db()
