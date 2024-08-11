from src.cli import AsyncDatabaseManager
from src.conf import celery_app


@celery_app.task()
def dump_db():
    db_manager = AsyncDatabaseManager()
    db_manager.dump_db()
