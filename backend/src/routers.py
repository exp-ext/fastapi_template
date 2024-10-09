from uuid import UUID
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from src.auth.routers import auth_router, users_router
from src.media.routers import media_router
from src.tgbot.routers import tg_router
from src.users.routers import account_router
from src.websocket import manager

templates = Jinja2Templates(directory="src/templates")
main_router = APIRouter()
main_router.include_router(auth_router, prefix="/auth", tags=["auth"])
main_router.include_router(users_router, prefix="/users", tags=["users"])
main_router.include_router(account_router, prefix="/users-account", tags=["users-account"])
main_router.include_router(media_router, prefix="/assets", tags=["assets"])
main_router.include_router(tg_router, prefix="/bot", tags=["tgbot"])


@main_router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@main_router.websocket("/ws/{chat_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: UUID, client_id: int):
    await manager.connect(websocket, chat_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message_to_chat(f"Client #{client_id} says: {data}", chat_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
        await manager.send_message_to_chat(f"Client #{client_id} left the chat", chat_id)
