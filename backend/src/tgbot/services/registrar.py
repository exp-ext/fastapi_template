import json
import secrets
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from src.conf.redis import AsyncRedisClient
from src.crud import tg_group_dao, user_ai_model_dao
from src.crud.user_crud import get_user_manager_without_db_session
from src.db.deps import get_async_session
from src.models import User
from src.schemas.tg_group_schema import TgGroupCreate
from telegram import Chat


class UserRedisManager:
    def __init__(self):
        self.redis_client = AsyncRedisClient.get_client()

    async def set_user_in_redis(self, tg_user, user: User) -> dict:
        """Обновляет запись в Redis db."""
        redis_user = {
            'user_id': str(user.id) if user else None,
            'tg_user_id': tg_user.id,
            'groups_connections': [group.id for group in user.tg_groups],
            'is_blocked_bot': user.is_blocked_bot,
        }
        await self.redis_client.set(f"user:{tg_user.id}", json.dumps(redis_user))
        return redis_user

    async def get_or_create_user(self, tg_user, prefetch_related: List[str], session: AsyncSession) -> Tuple[dict, Optional[User]]:
        """Возвращает или создает пользователя в базе данных."""
        redis_key = f"user:{tg_user.id}"
        redis_user = await self.redis_client.get(redis_key)
        redis_user = json.loads(redis_user) if redis_user else None

        prefetch_related.extend(["tg_groups"])

        user_manager = await get_user_manager_without_db_session(session)
        user = await user_manager.get_with_prefetch_related(tg_id=tg_user.id, prefetch_related=prefetch_related)

        if not user:
            kwargs = {
                "email": f"{tg_user.id}@telegram.com",
                "tg_username": tg_user.username or f'n-{str(1010101 + user.id)[::-1]}',
                "first_name": tg_user.first_name,
                "last_name": tg_user.last_name,
                "password": secrets.token_urlsafe(20),
                "is_active": True,
                "is_superuser": False,
            }
            await user_manager.get_or_create_by_tg_id(tg_id=tg_user.id, **kwargs)
            user = await user_manager.get_with_prefetch_related(tg_id=tg_user.id, prefetch_related=prefetch_related)
            await user_ai_model_dao.create_default(user=user, db_session=session)

        redis_user = await self.set_user_in_redis(tg_user, user)
        return redis_user, user


async def get_user(tg_user, chat, allow_unregistered: bool = False, prefetch_related: list = []) -> User | None:
    """Проверяет регистрацию пользователя или создает его."""
    redis_user_manager = UserRedisManager()

    async for session in get_async_session():

        red_user, user = await redis_user_manager.get_or_create_user(tg_user, prefetch_related, session)

        if red_user.get('is_blocked_bot') and not allow_unregistered:
            return None

        if chat.type != Chat.PRIVATE:
            group = await tg_group_dao.get_by_chat_id(chat_id=chat['id'], db_session=session)
            if not group:
                obj_in = TgGroupCreate(chat_id=chat.id, title=chat.title, link=chat.link)
                group = await tg_group_dao.create(obj_in=obj_in, db_session=session)

            if user and (group.id not in red_user.get('groups_connections')):
                user_manager = await get_user_manager_without_db_session(session)
                user = await user_manager.add_group(user=user, group=group)
                await redis_user_manager.set_user_in_redis(tg_user, user)

        return user
