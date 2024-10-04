from pydantic import BaseModel
from typing import Optional


class TgGroupCreate(BaseModel):
    chat_id: int
    title: Optional[str] = None
    link: Optional[str] = None


class TgGroupUpdate(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None


class TgGroupRead(BaseModel):
    id: int
    chat_id: int
    title: Optional[str] = None
    link: Optional[str] = None

    class Config:
        from_attributes = True
