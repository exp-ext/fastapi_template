from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.crud.base_crud import GenericCRUD
from src.models import TgGroup, TgUser
from src.schemas.tg_user_schema import TgUserCreate, TgUserUpdate


class TgUserDAO(GenericCRUD[TgUser, TgUserCreate, TgUserUpdate]):

    async def get_with_prefetch_related(
        self, *, id: int | str, prefetch_related: List, db_session: AsyncSession | None = None
    ) -> TgUser | None:
        query = select(TgUser).where(TgUser.id == id)
        load_options = [selectinload(getattr(TgUser, attr)) for attr in prefetch_related]
        query = query.options(*load_options)
        result = await db_session.execute(query)
        return result.scalars().first()

    async def add_group(
        self, *, user: TgUser, group: TgGroup, db_session: AsyncSession | None = None
    ) -> TgUser | None:
        user.groups.append(group)
        await db_session.commit()
        await db_session.refresh(user, ["groups"])
        return user


tg_user_dao = TgUserDAO(TgUser)
