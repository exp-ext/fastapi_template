from typing import TYPE_CHECKING, List

from sqlalchemy import DECIMAL, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import ChoiceType
from src.models.base_model import Base
from src.models.interim_tables import approved_user_models
from src.schemas.common_schema import ConsumerEnum, ProviderEnum

if TYPE_CHECKING:
    from src.models import User


class AIModels(Base):
    __tablename__ = 'ai_models'

    provider: Mapped[ProviderEnum] = mapped_column(
        ChoiceType(ProviderEnum, impl=String()),
        nullable=False,
        default=ProviderEnum.OPEN_AI,
    )
    title_public: Mapped[str] = mapped_column(String(28), nullable=False)
    title_model: Mapped[str] = mapped_column(String(28), nullable=False)
    api_key: Mapped[str] = mapped_column(String(100), nullable=False)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)

    incoming_price: Mapped[DECIMAL] = mapped_column(DECIMAL(6, 2), default=0)
    outgoing_price: Mapped[DECIMAL] = mapped_column(DECIMAL(6, 2), default=0)

    context_window: Mapped[int] = mapped_column(Integer, nullable=False)
    max_request_token: Mapped[int] = mapped_column(Integer, nullable=False)
    time_window: Mapped[int] = mapped_column(Integer, default=30)

    consumer: Mapped[ConsumerEnum] = mapped_column(
        ChoiceType(ConsumerEnum, impl=String()),
        nullable=False,
        default=ConsumerEnum.FAST_CHAT,
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=approved_user_models,
        back_populates="approved_user_models"
    )


class GPTPrompt(Base):
    __tablename__ = 'gpt_prompts'

    title: Mapped[str] = mapped_column(String(28), nullable=False)

    en_prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    ru_prompt_text: Mapped[str] = mapped_column(Text, nullable=False)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    consumer: Mapped[ConsumerEnum] = mapped_column(
        ChoiceType(ConsumerEnum, impl=String()),
        nullable=False,
        default=ConsumerEnum.FAST_CHAT,
    )
