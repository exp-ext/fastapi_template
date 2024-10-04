from sqlalchemy import select, cast, String
from src.crud.base_crud import GenericCRUD
from src.models import TgGroup
from src.schemas.tg_group_schema import TgGroupCreate, TgGroupUpdate
from sqlalchemy.ext.asyncio import AsyncSession


class TgGroupDAO(GenericCRUD[TgGroup, TgGroupCreate, TgGroupUpdate]):

    async def get_by_chat_id(self, *, chat_id: int, db_session: AsyncSession | None = None) -> TgGroup | None:
        group = await db_session.execute(select(TgGroup).where(cast(TgGroup.chat_id, String) == str(chat_id)))
        return group.scalars().first()


tg_group_dao = TgGroupDAO(TgGroup)
