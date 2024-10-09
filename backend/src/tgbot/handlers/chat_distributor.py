import asyncio

import httpx
from src.ai.gpt.open_ai import OpenAIProvider
from src.conf import settings
from src.conf.fastapi import ModeEnum
from src.tgbot.services.message_handler import send_message_to_chat
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..services.registrar import get_user

creativity_controls = {
    'temperature': 0.8,
    'top_p': 1,
    'max_tokens': 3000,
    'frequency_penalty': 0,
    'presence_penalty': 0,
}


async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allow_unregistered = True
    prefetch_related = ['active_model']
    return await get_user(
        tg_user=update.effective_user,
        chat=update.effective_chat,
        allow_unregistered=allow_unregistered,
        prefetch_related=prefetch_related,
    )


async def check_request_in_distributor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = 'http://127.0.0.1:8100/tasks/check/' if settings.MODE == ModeEnum.development else 'http://predict:8100/tasks/check/'
    text = update.effective_message.text
    chat_id = update.effective_chat.id
    data = {'text': text}

    async with httpx.AsyncClient() as client:
        user_task = asyncio.create_task(check_registration(update, context))
        post_task = asyncio.create_task(client.post(url, json=data))
        user, response = await asyncio.gather(user_task, post_task)

    creativity_controls = {
        'temperature': 0.8,
        'top_p': 1,
        'max_tokens': 3000,
        'frequency_penalty': 0,
        'presence_penalty': 0,
    }
    gpt_manager = OpenAIProvider(
        query_text=text,
        user=user,
        chat_id=chat_id,
        creativity_controls=creativity_controls
    )
    await gpt_manager.get_gpt_response()
    await send_message_to_chat(chat_id, gpt_manager.return_text, parse_mode=ParseMode.MARKDOWN)

    # completion = json.loads(response.content)

    # if completion['predicted_class'] == 'task':
    #     note_manager = ActionNoteManager(update, context, user)
    #     await note_manager.action_notes()
    # elif completion['predicted_class'] == 'weather':
    #     await distribution_current_weather(update, context, user)
    # else:
    #     gpt_manager = OpenAIProvider(
    #         query_text=text,
    #         user=user,
    #         chat_id=chat_id,
    #         creativity_controls=creativity_controls
    #     )
    #     await gpt_manager.get_gpt_response()


async def check_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await check_registration(update, context)
    text = update.effective_message.text
    chat_id = update.effective_chat.id
    gpt_manager = OpenAIProvider(
        query_text=text,
        user=user,
        chat_id=chat_id,
        creativity_controls=creativity_controls
    )
    await gpt_manager.get_gpt_response()
    await send_message_to_chat(chat_id, gpt_manager.return_text, parse_mode=ParseMode.MARKDOWN)


async def get_answer_chat_gpt_public(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_request_in_distributor(update, context)


async def get_answer_chat_gpt_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await check_request_in_distributor(update, context)
