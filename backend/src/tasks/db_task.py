from cli import AsyncDatabaseManager
from src.conf import taskiq_broker


@taskiq_broker.task
def dump_db():
    db_manager = AsyncDatabaseManager()
    db_manager.dump_db()
