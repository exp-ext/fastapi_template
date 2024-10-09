from typing import Dict, List
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.chats: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: UUID):
        await websocket.accept()
        if chat_id not in self.chats:
            self.chats[chat_id] = []
        self.chats[chat_id].append(websocket)

    def disconnect(self, websocket: WebSocket, chat_id: str):
        self.chats[chat_id].remove(websocket)
        if not self.chats[chat_id]:
            del self.chats[chat_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_message_to_chat(self, message: str, chat_id: str):
        if chat_id in self.chats:
            for connection in self.chats[chat_id]:
                await connection.send_text(message)


manager = ConnectionManager()
