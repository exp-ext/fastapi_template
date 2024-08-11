from celery import Celery
from celery.schedules import crontab
from kombu import Queue


class CeleryAppFactory:
    _celery_app = None

    @classmethod
    def get_celery_app(cls):
        from . import settings
        if cls._celery_app is None:
            cls._celery_app = Celery(
                "celery_app",
                broker=str(settings.CELERY_BROKER_URL),
                backend=str(settings.SYNC_CELERY_DATABASE_URI),
                include=("src.tasks.db_task",),
            )

            cls._celery_app.conf.update(
                {
                    'beat_dburi': str(settings.SYNC_CELERY_BEAT_DATABASE_URI),
                    'worker_log_level': 'INFO',
                    'beat_log_level': 'INFO',
                    'broker_transport_options': {
                        'max_retries': 5,
                        'interval_start': 0,
                        'interval_step': 0.5,
                        'interval_max': 3
                    },
                    'task_queues': (
                        Queue('celery_tasks', routing_key='celery_tasks.#'),
                    ),
                    'task_routes': {
                        'src.tasks.db_task.*': {'queue': 'celery_tasks'},
                    },
                }
            )
            cls._celery_app.autodiscover_tasks()
            cls._celery_app.conf.beat_schedule = {
                'dump_db': {
                    'task': 'src.tasks.db_task.dump_db',
                    'schedule': crontab(hour=3, minute=0)
                },
            }

        return cls._celery_app
