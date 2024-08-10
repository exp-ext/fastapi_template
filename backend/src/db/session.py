from sqlalchemy import QueuePool, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from src.conf import ModeEnum, settings

DB_POOL_SIZE = 83
WEB_CONCURRENCY = 9
POOL_SIZE = max(DB_POOL_SIZE // WEB_CONCURRENCY, 5)


engine = create_async_engine(
    str(settings.ASYNC_DATABASE_URI),
    echo=False,
    poolclass=NullPool if settings.MODE == ModeEnum.testing else AsyncAdaptedQueuePool,
    pool_size=POOL_SIZE,
    max_overflow=64,
)
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

engine = create_engine(
    str(settings.SYNC_DATABASE_URI),
    echo=False,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=64,
)
SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

engine_celery = create_async_engine(
    str(settings.ASYNC_CELERY_BEAT_DATABASE_URI),
    echo=False,
    poolclass=NullPool if settings.MODE == ModeEnum.testing else AsyncAdaptedQueuePool,
    pool_size=POOL_SIZE,
    max_overflow=64,
)
SessionLocalCelery = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_celery,
    class_=AsyncSession,
    expire_on_commit=False,
)
