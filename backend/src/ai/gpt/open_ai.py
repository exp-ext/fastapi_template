import asyncio
import json
import pprint

import httpx
import openai
import tiktoken_async
from httpx_socks import AsyncProxyTransport
from src.ai.gpt.abc_provider import BaseAIProvider
from src.ai.gpt.exception import (OpenAIConnectionError, OpenAIResponseError,
                                  UnhandledError, ValueChoicesError)
from src.conf import settings
from src.conf.fastapi import ModeEnum
from src.crud import ai_transaction_dao

from .mock_text_generator import client_mock, text_stream_generator


class OpenAIProvider(BaseAIProvider):

    async def httpx_request(self) -> None:
        """Делает запрос в OpenAI и выключает typing."""
        while True:
            try:
                proxy_transport = AsyncProxyTransport.from_url(settings.SOCKS5)
                async with httpx.AsyncClient(transport=proxy_transport) as transport:
                    if settings.MODE == ModeEnum.development:
                        client = client_mock
                        await asyncio.sleep(2)
                    else:
                        client = openai.AsyncClient(
                            api_key=self.model.api_key,
                            timeout=self.MAX_TYPING_TIME * 60,
                            http_client=transport,
                        )
                    completion = await client.chat.completions.create(
                        model=self.model.title_model,
                        messages=self.all_prompt,
                        **self.creativity_controls
                    )
                if hasattr(completion, 'choices'):
                    self.return_text = completion.choices[0].message.content.strip()
                    self.return_text_tokens = completion.usage.completion_tokens
                    self.query_text_tokens = completion.usage.prompt_tokens
                    return
                formatted_dict = pprint.pformat(completion.__dict__, indent=4)
                raise ValueChoicesError(f"`GetAnswerGPT`, ответ не содержит полей 'choices':\n{formatted_dict}")

            except openai.APIStatusError as http_err:
                raise OpenAIResponseError(f'`GetAnswerGPT`, ответ сервера был получен, но код состояния указывает на ошибку: {http_err}') from http_err

            except openai.APIConnectionError as req_err:
                raise OpenAIConnectionError(f'`GetAnswerGPT`, проблемы соединения: {req_err}') from req_err

            except Exception as error:
                raise UnhandledError(f'Необработанная ошибка в `GetAnswerGPT.httpx_request_to_openai()`: {error}') from error

    async def stream_request(self) -> None:
        """Делает запрос в OpenAI и выключает typing."""
        try:
            proxy_transport = AsyncProxyTransport.from_url(settings.SOCKS5)
            async with httpx.AsyncClient(transport=proxy_transport) as transport:
                client = openai.AsyncOpenAI(
                    api_key=self.model.api_key,
                    http_client=transport,
                )
                if settings.MODE == ModeEnum.development:
                    stream = text_stream_generator(chunk_size=20)
                else:
                    stream = await client.chat.completions.create(
                        model=self.model.title_model,
                        messages=self.all_prompt,
                        stream=True,
                        **self.creativity_controls
                    )
                first_chunk = True
                async for chunk in stream:
                    self.return_text += chunk.choices[0].delta.content or ""
                    await self.send_chunk_to_websocket(self.return_text, is_start=first_chunk, is_end=False)
                    if first_chunk:
                        first_chunk = False
                await self.send_chunk_to_websocket("", is_end=True)
                await self.finite_tokens()

        except openai.APIStatusError as http_err:
            raise OpenAIResponseError(f'`WSAnswerChatGPT`, ответ сервера был получен, но код состояния указывает на ошибку: {http_err}') from http_err
        except openai.APIConnectionError as req_err:
            raise OpenAIConnectionError(f'`WSAnswerChatGPT`, проблемы соединения: {req_err}') from req_err
        except Exception as error:
            raise UnhandledError(f'Необработанная ошибка в `WSAnswerChatGPT.httpx_request_to_openai()`: {error}') from error

    async def send_chunk_to_websocket(self, chunk: str, is_start: bool = False, is_end: bool = False):
        """Отправка части текста через веб-сокет с указанием на статус начала и конца потока."""
        message = {
            'message': chunk,
            'username': 'GPT',
            'is_stream': True,
            'is_start': is_start,
            'is_end': is_end,
        }
        await self.ws_manager.send_message_to_chat(json.dumps(message), self.chat_id)

    async def num_tokens(self, text: str, corr_token: int = 0) -> int:
        """Считает количество токенов.
        ## Args:
        - text (`str`): текс для которого возвращается количество
        - corr_token (`int`): количество токенов для ролей и разделителей

        """
        try:
            encoding = await tiktoken_async.encoding_for_model(self.model.title_model)
        except KeyError:
            encoding = await tiktoken_async.get_encoding("cl100k_base")
        return len(encoding.encode(text)) + corr_token

    async def get_prompt(self, session) -> None:
        """Prompt для запроса в OpenAI и модель user."""
        history = []
        await self.add_to_prompt('system', self.assist_prompt.en_prompt_text)

        if self.active_model:
            history = await ai_transaction_dao.get_history(
                user_ai_model_id=self.active_model.id, time_start=self.time_start, current_time=self.current_time, db_session=session
            )

        if self.reply_to_message_text:
            reply_to_message_tokens = await self.num_tokens(self.reply_to_message_text, 4)
            self.query_text_tokens += reply_to_message_tokens

        token_counter = self.query_text_tokens + self.assist_prompt_tokens
        for item in history:
            question_tokens = item.get('question_tokens', 0)
            answer_tokens = item.get('answer_tokens', 0)
            # +11 - токены для ролей и разделителей: 'system' - 7 'user' - 4
            token_counter += question_tokens + answer_tokens + 11

            if token_counter >= self.model.context_window:
                break

            await self.add_to_prompt('user', item['question'])
            await self.add_to_prompt('assistant', item['answer'])

        if self.reply_to_message_text:
            await self.remove_from_prompt('assistant', self.reply_to_message_text)
            await self.add_to_prompt(
                'assistant', f'A message to analyze that you are asked to respond to: {self.reply_to_message_text}'
            )

        await self.add_to_prompt('user', self.query_text)
