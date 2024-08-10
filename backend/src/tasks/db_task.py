from src.cli import DatabaseManager
from src.conf import celery_app


@celery_app.task()
def dump_db():
    db_manager = DatabaseManager()
    db_manager.dump_db()
