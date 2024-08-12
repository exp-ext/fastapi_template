from typing import AsyncGenerator

from fastapi import Depends, Request
from fastapi_users.db import SQLAlchemyUserDatabase
from redis.asyncio import ConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import async_session, sync_session
from src.models import User
from taskiq import TaskiqDepends


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_sync_session() -> AsyncGenerator[AsyncSession, None]:
    async with sync_session() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


def get_redis_pool(request: Request = TaskiqDepends()) -> ConnectionPool:
    return request.app.state.redis_pool
