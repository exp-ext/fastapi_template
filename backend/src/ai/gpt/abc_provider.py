import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Set, Type
from uuid import UUID

import markdown
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta
from src.ai.gpt.exception import InWorkError, LongQueryError, handle_exceptions
from src.conf.redis import AsyncRedisClient
from src.crud import (ai_model_dao, ai_transaction_dao, gpt_prompt_dao,
                      user_ai_model_dao)
from src.db.deps import get_async_session
from src.models.ai_model import AIModels
from src.models.user_model import User
from src.schemas.ai_transaction_schema import AITransactionCreate
from src.schemas.common_schema import ConsumerEnum
from src.tgbot.loader import bot
from src.utils.re_compile import PUNCTUATION_RE
from src.websocket import manager


class ABCProvider(ABC):

    @abstractmethod
    async def num_tokens(self, text: str, corr_token: int = 0) -> int:
        pass

    @abstractmethod
    async def get_prompt(self, session) -> None:
        pass

    @abstractmethod
    async def httpx_request(self):
        pass

    @abstractmethod
    async def stream_request(self):
        pass


class BaseAIProvider(ABCProvider):

    MAX_TYPING_TIME = 5  # Максимальное время для TYPING в минутах

    def __init__(
        self, query_text: str, user: Type[DeclarativeMeta],
        chat_id: int | UUID = None, creativity_controls: Dict[str, Any] = {},
        consumer: Enum = ConsumerEnum.FAST_CHAT, stream: bool = False, tg_chat: bool = True
    ) -> None:
        # Инициализация свойств класса
        self.user: User = user                    # модель пользователя пославшего запрос
        self.query_text: str = query_text        # текст запроса пользователя
        self.chat_id: int | UUID = chat_id       # id чата
        self.creativity_controls: dict = creativity_controls      # параметры которые контролируют креативность и разнообразие текста
        self.consumer: ConsumerEnum = consumer            # потребитель запроса для истории
        self.stream = stream

        # Дополнительные свойства
        self.query_text_tokens: int = 0       # количество токенов в запросе
        self.assist_prompt_tokens: int = 0     # количество токенов в промпте ассистента в head модели
        self.return_text_tokens: int = 0      # количество токенов в ответе
        self.all_prompt: list = []                # общий промпт для запроса
        self.current_time = datetime.now(timezone.utc)  # текущее время для окна истории
        self.time_start = None              # время начала для окна истории
        self.event = asyncio.Event() if tg_chat else None  # typing в чат пользователя
        self.model: AIModels | None = None                   # активная модель пользователя
        self.assist_prompt = None           # активный системный промпт пользователя
        self.return_text = ''               # текст полученный в ответе от модели
        self.reply_to_message_text = None   # текст в случает запроса на ответ GPT
        self.active_model = None
        self.redis_client = AsyncRedisClient.get_client()
        self.ws_manager = manager if stream else None
        self.history_crud = ai_transaction_dao

    @property
    def check_long_query(self) -> bool:
        return self.query_text_tokens > self.model.max_request_token

    @staticmethod
    def clean_and_split_text(text: str, word_limit=15) -> Set:
        """
        Функция для удаления HTML и Markdown разметки и очистки текста от знаков препинания.
        Возвращает множество по умолчанию до 15 первых уникальных слов.
        """
        html_text = markdown.markdown(text)
        soup = BeautifulSoup(html_text, "html.parser")
        clean_text = soup.get_text()

        clean_text = PUNCTUATION_RE.sub('', clean_text)
        words = clean_text.split()

        return set(words[:word_limit])

    async def init_model_config(self, session: AsyncSession):
        if self.user:
            self.active_model = await user_ai_model_dao.get_active_model(user=self.user, db_session=session)
            if not self.active_model:
                self.active_model = await user_ai_model_dao.create_default(self.user, db_session=session)
            config_source = self.active_model
        else:
            config_source = {
                "model": await ai_model_dao.get_default(db_session=session),
                "prompt": await gpt_prompt_dao.get_default(db_session=session),
                "time_start": self.current_time,
            }
        self.model = config_source.get("model") if isinstance(config_source, dict) else config_source.model
        self.assist_prompt = config_source.get("prompt") if isinstance(config_source, dict) else config_source.prompt
        self.time_start = config_source.get("time_start") if isinstance(config_source, dict) else config_source.time_start

    async def create_history(self):
        obj_in = AITransactionCreate(
            user_id=self.user.id if self.user else None,
            chat_id=str(self.chat_id),
            question=self.query_text,
            question_tokens=self.query_text_tokens,
            question_token_price=self.model.outgoing_price,
            answer=self.return_text,
            answer_tokens=self.return_text_tokens,
            answer_token_price=self.model.incoming_price,
            consumer=self.consumer,
            user_ai_model_id=self.active_model.id if self.active_model else None
        )
        async for session in get_async_session():
            await self.history_crud.create(obj_in=obj_in, db_session=session)

    async def get_gpt_response(self) -> dict:
        """Основная логика."""
        try:
            async for session in get_async_session():

                await self.init_model_config(session)

                self.query_text_tokens, self.assist_prompt_tokens, _ = await asyncio.gather(
                    self.num_tokens(self.query_text, 4),
                    self.num_tokens(self.assist_prompt.en_prompt_text, 7),
                    self.check_in_works(),
                )

                if self.check_long_query:
                    raise LongQueryError(
                        'Слишком большой текст запроса.\nПопробуйте сформулировать его короче.'
                    )

                if self.event:
                    asyncio.create_task(self.send_typing_periodically_for_tg_bot())

                await self.get_prompt(session)

            if self.stream and self.is_valid_uuid(self.chat_id):
                await self.stream_request()
            else:
                await self.httpx_request()

            asyncio.create_task(self.create_history())

            await self.response_processing()

        except Exception as err:
            _, type_err, traceback_str = await handle_exceptions(err, True)
            raise type_err(f'\n\n{str(err)}{traceback_str}')
        finally:
            await self.del_mess_in_redis()
            if self.event:
                self.event.set()

    async def response_processing(self):
        pass

    def is_valid_uuid(self, chat_id):
        try:
            UUID(str(chat_id))
            return True
        except ValueError:
            raise ValueError("chat_id is not a valid UUID")

    async def remove_from_prompt(self, role: str, text: str) -> None:
        """Удалить последнюю запись из списка all_prompt, если первые 15 слов совпадают без учета HTML и Markdown тегов."""
        if not self.all_prompt:
            return

        last_prompt = self.all_prompt[-1]

        if last_prompt['role'] == role:

            last_prompt_words = self.clean_and_split_text(last_prompt['content'])
            input_text_words = self.clean_and_split_text(text)

            if last_prompt_words == input_text_words:
                del self.all_prompt[-1]

    async def add_to_prompt(self, role: str, content: str) -> None:
        """Добавляет элемент в список all_prompt."""
        self.all_prompt.append({'role': role, 'content': content})

    async def send_typing_periodically_for_tg_bot(self) -> None:
        """"Передаёт TYPING в чат Телеграм откуда пришёл запрос."""
        time_stop = datetime.now() + timedelta(minutes=self.MAX_TYPING_TIME)
        while not self.event.is_set():
            await bot.send_chat_action(chat_id=self.chat_id, action='typing')
            await asyncio.sleep(2)
            if datetime.now() > time_stop:
                break

    async def check_in_works(self) -> bool:
        """Проверяет нет ли уже в работе этого запроса в Redis и добавляет его."""
        queries = await self.redis_client.lrange(f'gpt_user:{self.chat_id}', 0, -1)
        if self.query_text in queries:
            raise InWorkError('Запрос уже находится в работе.')
        await self.redis_client.lpush(f'gpt_user:{self.chat_id}', self.query_text)

    async def del_mess_in_redis(self) -> None:
        """Удаляет входящее сообщение из Redis."""
        await self.redis_client.lrem(f'gpt_user:{self.chat_id}', 1, self.query_text.encode('utf-8'))

    async def finite_tokens(self):
        all_prompt_text = "".join(["".join(["{}: {}".format(key, value) for key, value in item.items()]) for item in self.all_prompt])
        self.query_text_tokens, self.return_text_tokens = await asyncio.gather(
            self.num_tokens(all_prompt_text),
            self.num_tokens(self.return_text, 4),
        )
