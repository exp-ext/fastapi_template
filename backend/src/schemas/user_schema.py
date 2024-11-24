import uuid
from typing import Optional

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tg_id: Optional[int] = None
    tg_username: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tg_id: Optional[int] = None
    tg_username: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tg_id: Optional[int] = None
    tg_username: Optional[str] = None
