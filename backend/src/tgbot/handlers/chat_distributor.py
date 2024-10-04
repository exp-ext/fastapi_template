import asyncio
import json

import httpx
from src.conf import settings
from src.conf.fastapi import ModeEnum
from src.db.deps import get_async_session
from telegram import Update
from telegram.ext import ContextTypes

from ..registrar import get_user


async def async_check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allow_unregistered = True
    prefetch_related = []
    async for session in get_async_session():
        return await get_user(
            tg_user=update.effective_user,
            chat=update.effective_chat,
            allow_unregistered=allow_unregistered,
            prefetch_related=prefetch_related,
            session=session
        )


async def check_request_in_distributor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = 'http://127.0.0.1:8100/tasks/check/' if settings.MODE == ModeEnum.development else 'http://predict:8100/tasks/check/'
    text = update.effective_message.text
    data = {'text': text}

    async with httpx.AsyncClient() as client:
        user_task = asyncio.create_task(async_check_registration(update, context))
        post_task = asyncio.create_task(client.post(url, json=data))
        user, response = await asyncio.gather(user_task, post_task)

    completion = json.loads(response.content)

    # if completion['predicted_class'] == 'task' and 'напом' in text.lower():
    #     note_manager = ActionNoteManager(update, context, user)
    #     await note_manager.action_notes()
    # elif completion['predicted_class'] == 'weather':
    #     await distribution_current_weather(update, context, user)
    # else:
    #     get_answer = TelegramAnswerGPT(update, context, user)
    #     await get_answer.answer_from_ai()


async def check_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await async_check_registration(update, context)
    pass
    # get_answer = TelegramAnswerGPT(update, context, user)
    # await get_answer.answer_from_ai()


async def get_answer_chat_gpt_public(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_request_in_distributor(update, context)


async def get_answer_chat_gpt_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await check_request_in_distributor(update, context)
