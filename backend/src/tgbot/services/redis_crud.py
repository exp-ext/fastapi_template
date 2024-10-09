import json

from src.conf.redis import AsyncRedisClient


class RedisCRUDManager:
    def __init__(self, pattern):
        self.redis_client = AsyncRedisClient.get_client()
        self.pattern = pattern

    async def save_message_id(self, chat_id, message_id):
        """Сохраняет message_id в Redis, используя chat_id как ключ"""
        key = f"tgbot_chat:{chat_id}:{self.pattern}"
        await self.redis_client.sadd(key, message_id)

    async def get_message_ids(self, chat_id):
        """Получает все message_id для chat_id"""
        key = f"tgbot_chat:{chat_id}:{self.pattern}"
        return await self.redis_client.smembers(key)

    async def delete_messages_for_chat_id(self, chat_id):
        """Удаляет все сохранённые message_id для chat_id, если они существуют"""
        key = f"tgbot_chat:{chat_id}:{self.pattern}"
        if await self.redis_client.exists(key):
            await self.redis_client.delete(key)

    async def update_user_data_in_redis(self, user_data):
        """Обновляет данные пользователя."""
        async with self.redis_client.pipeline(transaction=True) as pipe:
            for user in user_data:
                key = f"{self.pattern}:{int(user['tg_id'])}"
                value = json.dumps(user)
                await pipe.set(key, value)
            await pipe.execute()

    async def fetch_user_data_from_redis(self, user_tg_id):
        """Извлекает данные пользователя по `user_id`."""
        key = f"{self.pattern}:{user_tg_id}"
        value = await self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None
