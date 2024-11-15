import json

from src.conf.redis import AsyncRedisClient


class RedisCRUDManager:
    def __init__(self, pattern):
        self.redis_client = AsyncRedisClient.get_client()
        self.pattern = pattern

    def _get_key(self, chat_id):
        """Возвращает ключ для Redis с заданным chat_id."""
        return f"telbot_chat:{chat_id}:{self.pattern}"

    async def save_message_id(self, chat_id, message_id):
        """Сохраняем message_id в Redis, используя chat_id как ключ"""
        await self.redis_client.sadd(self._get_key(chat_id), message_id)

    async def get_message_ids(self, chat_id):
        """Получаем все message_id для chat_id"""
        return await self.redis_client.smembers(self._get_key(chat_id))

    async def delete_messages_for_chat_id(self, chat_id):
        """Удаляем все сохранённые message_id для chat_id, если они существуют"""
        key = self._get_key(chat_id)
        if await self.redis_client.exists(key):
            await self.redis_client.delete(key)

    async def update_user_data_in_redis(self, user_data):
        """Обновляем данные пользователя."""
        async with self.redis_client.pipeline(transaction=True) as pipe:
            for user in user_data:
                key = f"{self.pattern}:{int(user['tg_id'])}"
                value = json.dumps(user)
                await pipe.set(key, value)
            await pipe.execute()

    async def fetch_user_data_from_redis(self, user_tg_id):
        """Извлекаем данные пользователя по `user_tg_id`."""
        key = f"{self.pattern}:{user_tg_id}"
        value = await self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None
