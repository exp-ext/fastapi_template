from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from src.conf import settings
from src.tgbot.loader import application
from telegram import Update

tg_router = APIRouter()


@tg_router.post(f"/{settings.SECRET_BOT_URL}/webhooks/", status_code=status.HTTP_200_OK)
async def receive_update(request: Request):
    await application.update_queue.put(
        Update.de_json(data=await request.json(), bot=application.bot)
    )
    return JSONResponse(content={"ok": True})
