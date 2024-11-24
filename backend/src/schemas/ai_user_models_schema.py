from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class UserAIModelCreate(BaseModel):
    user_id: Optional[uuid.UUID] = Field(None, description="ID пользователя")
    model_id: Optional[uuid.UUID] = Field(None, description="ID модели ИИ")
    prompt_id: Optional[uuid.UUID] = Field(None, description="ID GPT промпта")

    class Config:
        from_attributes = True
        protected_namespaces = ()


class UserAIModelUpdate(BaseModel):
    user_id: Optional[uuid.UUID] = Field(None, description="ID пользователя")
    model_id: Optional[uuid.UUID] = Field(None, description="ID модели ИИ")
    prompt_id: Optional[uuid.UUID] = Field(None, description="ID GPT промпта")

    class Config:
        from_attributes = True
        protected_namespaces = ()


class UserAIModelRead(BaseModel):
    id: uuid.UUID
    time_start: datetime
    user_id: Optional[uuid.UUID]
    model_id: Optional[uuid.UUID]
    prompt_id: Optional[uuid.UUID]

    class Config:
        from_attributes = True
        protected_namespaces = ()
