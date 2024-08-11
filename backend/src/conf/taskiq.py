from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend
from aio_pika import ExchangeType
from . import settings

taskiq_app = AioPikaBroker(
    f"amqp://{settings.RABBITMQ_DEFAULT_USER}:{settings.RABBITMQ_DEFAULT_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}",
    queue_name="taskiq_tasks",
    routing_key="taskiq_tasks_key",
    exchange_name="taskiq_exchange",
    exchange_type=ExchangeType.DIRECT
).with_result_backend(
    RedisAsyncResultBackend(f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}")
)


scheduler = TaskiqScheduler(
    broker=taskiq_app,
    sources=[LabelScheduleSource(taskiq_app)],
)
