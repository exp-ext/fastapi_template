from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from sqladmin import Admin
from src.admin import ImageAdmin, UserAdmin
from src.admin.auth import AdminAuth
from src.conf import settings, taskiq_broker
from src.conf.redis import set_async_redis_client
from src.db.session import engine
from src.routers import main_router
from src.tgbot.dispatcher import setup_handlers
from src.tgbot.loader import application
from starlette.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis_client = await set_async_redis_client()
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    await FastAPICache.clear()

    if not taskiq_broker.is_worker_process:
        await taskiq_broker.startup()

    await setup_handlers(application)
    async with application:
        await application.start()
        yield
        await application.stop()

    if not taskiq_broker.is_worker_process:
        await taskiq_broker.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(main_router)

app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.mount("/templates", StaticFiles(directory="src/templates"), name="templates")

admin = Admin(app, engine, authentication_backend=AdminAuth())
admin.add_view(UserAdmin)
admin.add_view(ImageAdmin)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
