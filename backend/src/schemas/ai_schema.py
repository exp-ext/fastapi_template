from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field
from src.models.common_models import ConsumerEnum, ProviderEnum


class AIModelCreate(BaseModel):
    provider: ProviderEnum = ProviderEnum.OPEN_AI
    title_public: str = Field(max_length=28)
    title_model: str = Field(max_length=28)
    api_key: str = Field(max_length=100)
    is_default: bool = False
    is_free: bool = False
    incoming_price: Decimal = Field(default=0, max_digits=6, decimal_places=2)
    outgoing_price: Decimal = Field(default=0, max_digits=6, decimal_places=2)
    context_window: int
    max_request_token: int
    time_window: int = 30
    consumer: ConsumerEnum = ConsumerEnum.FAST_CHAT

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class AIModelUpdate(BaseModel):
    provider: Optional[ProviderEnum] = None
    title_public: Optional[str] = Field(None, max_length=28)
    title_model: Optional[str] = Field(None, max_length=28)
    api_key: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None
    is_free: Optional[bool] = None
    incoming_price: Optional[Decimal] = Field(None, max_digits=6, decimal_places=2)
    outgoing_price: Optional[Decimal] = Field(None, max_digits=6, decimal_places=2)
    context_window: Optional[int] = None
    max_request_token: Optional[int] = None
    time_window: Optional[int] = None
    consumer: Optional[ConsumerEnum] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class GPTPromptCreate(BaseModel):
    title: str = Field(max_length=28)
    en_prompt_text: str
    ru_prompt_text: str
    is_default: bool = False
    consumer: ConsumerEnum = ConsumerEnum.FAST_CHAT

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class GPTPromptUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=28)
    en_prompt_text: Optional[str] = None
    ru_prompt_text: Optional[str] = None
    is_default: Optional[bool] = None
    consumer: Optional[ConsumerEnum] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
