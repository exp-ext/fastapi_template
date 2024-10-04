from typing import Optional

from pydantic import BaseModel


class TgUserCreate(BaseModel):
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_blocked_bot: Optional[bool] = True


class TgUserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_blocked_bot: Optional[bool] = None


class TgUserRead(BaseModel):
    id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    is_blocked_bot: bool

    class Config:
        from_attributes = True
