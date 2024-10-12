from src.db.deps import get_user_db
from sqlalchemy.ext.asyncio import AsyncSession
import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from src.ai.gpt.open_ai import OpenAIProvider
from src.auth.routers import auth_router, users_router
from src.crud.user_crud import authenticate_websocket_user
from src.media.routers import media_router
from src.models.user_model import User
from src.tgbot.routers import tg_router
from src.users.routers import account_router
from src.websocket import manager

main_router = APIRouter()
main_router.include_router(auth_router, prefix="/api/auth", tags=["auth"])
main_router.include_router(users_router, prefix="/api/users", tags=["users"])
main_router.include_router(account_router, prefix="/api/users-account", tags=["users-account"])
main_router.include_router(media_router, prefix="/api/assets", tags=["assets"])
main_router.include_router(tg_router, prefix="/bot", tags=["tgbot"])


async def get_optional_user(
    token: Optional[str] = Query(None),
    user_db: AsyncSession = Depends(get_user_db)
) -> Optional[User]:
    """
    Получаем пользователя на основе токена из WebSocket.
    """
    if token:
        user = await authenticate_websocket_user(token, user_db)
        return user
    return None


@main_router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket, chat_id: UUID, user: Optional[User] = Depends(get_optional_user),
):
    await manager.connect(websocket, chat_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                data_json = json.loads(data)
                text = data_json.get('text', '')
            except json.JSONDecodeError:
                text = data

            if text:
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
                    creativity_controls=creativity_controls,
                    stream=True,
                    tg_chat=False
                )
                await gpt_manager.get_gpt_response()
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
