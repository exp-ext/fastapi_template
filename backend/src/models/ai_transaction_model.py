import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import ChoiceType
from src.models.base_model import Base
from src.models.common_models import ConsumerEnum

if TYPE_CHECKING:
    from src.models import UserAIModel


class AITransactions(Base):
    __tablename__ = 'ai_transactions'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[str] = mapped_column(String(128), nullable=True)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    question_token_price: Mapped[DECIMAL] = mapped_column(DECIMAL(6, 2), default=0)

    answer: Mapped[str] = mapped_column(Text, nullable=False)
    answer_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_token_price: Mapped[DECIMAL] = mapped_column(DECIMAL(6, 2), default=0)

    image: Mapped[str] = mapped_column(String, nullable=True)

    consumer: Mapped[ConsumerEnum] = mapped_column(
        ChoiceType(ConsumerEnum, impl=String()),
        nullable=False,
        default=ConsumerEnum.FAST_CHAT,
    )

    user_ai_model_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('user_ai_models.id'), nullable=True)
    user_ai_model: Mapped[Optional["UserAIModel"]] = relationship("UserAIModel", foreign_keys=[user_ai_model_id])
