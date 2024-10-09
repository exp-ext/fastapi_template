import json
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from src.conf.redis import AsyncRedisClient
from src.crud import tg_group_dao, tg_user_dao, user_ai_model_dao
from src.db.deps import get_async_session
from src.models import TgGroup, TgUser
from src.schemas.tg_user_schema import TgUserCreate


class UserRedisManager:
    def __init__(self):
        self.redis_client = AsyncRedisClient.get_client()

    async def set_user_in_redis(self, tg_user, user: TgUser) -> dict:
        """Обновляет запись в Redis db."""
        redis_user = {
            'user_id': user.user.id if user.user else None,
            'tg_user_id': tg_user.id,
            'groups_connections': [group.id for group in user.groups],
            'is_blocked_bot': user.is_blocked_bot,
        }
        await self.redis_client.set(f"user:{tg_user.id}", json.dumps(redis_user))
        return redis_user

    async def get_or_create_user(self, tg_user, prefetch_related: List[str], session: AsyncSession) -> Tuple[dict, Optional[TgUser]]:
        """Возвращает или создает пользователя в базе данных."""
        redis_key = f"user:{tg_user.id}"
        redis_user = await self.redis_client.get(redis_key)
        redis_user = json.loads(redis_user) if redis_user else None

        prefetch_related.extend(["groups", "user", "active_model"])
        user = await tg_user_dao.get_with_prefetch_related(id=tg_user.id, prefetch_related=prefetch_related, db_session=session)

        if not user:
            obj_in = TgUserCreate(
                id=tg_user.id,
                username=tg_user.username or f'n-{str(1010101 + tg_user.id)[::-1]}',
                first_name=tg_user.first_name or tg_user.username,
                last_name=tg_user.last_name
            )
            user = await tg_user_dao.create(obj_in=obj_in, db_session=session, relationship_refresh=prefetch_related)
            await user_ai_model_dao.create_default(user=user, db_session=session)

        redis_user = await self.set_user_in_redis(tg_user, user)
        return redis_user, user


async def get_user(tg_user, chat, allow_unregistered: bool = False, prefetch_related: list = []) -> TgUser | None:
    """Проверяет регистрацию пользователя или создает его."""
    user_manager = UserRedisManager()

    async for session in get_async_session():

        red_user, user = await user_manager.get_or_create_user(tg_user, prefetch_related, session)

        if red_user.get('is_blocked_bot') and not allow_unregistered:
            return None

        if chat.type != 'private':
            group = await tg_group_dao.get_by_chat_id(chat_id=chat['id'], db_session=session)
            if not group:
                obj_in = TgGroup(chat_id=chat.id, title=chat.title, link=chat.link)
                group = await tg_group_dao.create(obj_in=obj_in, db_session=session)

            if user and (group.id not in red_user.get('groups_connections')):
                user = await tg_user_dao.add_group(user=user, group=group, db_session=session)
                await user_manager.set_user_in_redis(tg_user, user)

        return user
