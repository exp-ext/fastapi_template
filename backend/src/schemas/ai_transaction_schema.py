import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field
from src.schemas.common_schema import ConsumerEnum


class AITransactionCreate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    chat_id: Optional[str] = None
    question: str
    question_tokens: Optional[int] = None
    question_token_price: Decimal = Field(default=Decimal("0.00"), max_digits=6, decimal_places=2)
    answer: str
    answer_tokens: Optional[int] = None
    answer_token_price: Decimal = Field(default=Decimal("0.00"), max_digits=6, decimal_places=2)
    image: Optional[str] = None
    consumer: ConsumerEnum = ConsumerEnum.FAST_CHAT
    user_ai_model_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
