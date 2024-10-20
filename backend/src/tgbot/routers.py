import asyncio

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from src.conf import settings
from src.tgbot.loader import application
from src.tgbot.services.cleaner import clear_commands
from telegram import Update

tg_router = APIRouter()


@tg_router.post(f"/{settings.SECRET_BOT_URL}/webhooks/", status_code=status.HTTP_200_OK)
async def receive_update(request: Request):
    """
    Получает обновления от серверов Telegram через вебхук.
    Преобразует входящий JSON в объект Update и отправляет его в очередь на обработку.
    """
    update = Update.de_json(data=await request.json(), bot=application.bot)
    if update.message:
        asyncio.create_task(clear_commands(update))
    await application.update_queue.put(update)
    return JSONResponse(content={"ok": True})
