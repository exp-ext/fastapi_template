from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from src.conf import settings
from src.conf.redis import set_async_redis_client
from src.routers import main_router
from starlette.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis_client = await set_async_redis_client()
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    await FastAPICache.clear()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(main_router)

app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.mount("/templates", StaticFiles(directory="src/templates"), name="templates")


app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=str(settings.ASYNC_DATABASE_URI),
    engine_args={
        "echo": True,  # SQLAlchemy будет выводить в консоль (или в лог) все SQL-запросы, которые выполняет, вместе с их параметрами.
        "future": True,  # включает новые функции и изменения в API SQLAlchemy, которые были добавлены в более поздних версиях (начиная с SQLAlchemy 1.4).
        "pool_size": 10,  # Размер пула соединений. Определяет, сколько соединений с базой данных будет поддерживаться одновременно.
        "max_overflow": 20,  # Количество дополнительных соединений, которые могут быть открыты сверх pool_size.
        "pool_timeout": 30,  # Время ожидания перед тем, как будет выброшено исключение, если пул соединений занят.
        "pool_pre_ping": True  # Если установлено в True, SQLAlchemy будет отправлять запрос SELECT 1 перед использованием соединения из пула, чтобы убедиться, что оно еще активное.
    }
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
