import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import DECIMAL, Boolean
from sqlalchemy_utils import ChoiceType
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_model import Base
from src.models.common_models import ConsumerEnum, ProviderEnum
from src.models.interim_tables import approved_user_models

if TYPE_CHECKING:
    from src.models import TgUser, User


class AIModels(Base):
    __tablename__ = 'ai_models'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
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

    tg_users: Mapped[List["TgUser"]] = relationship(
        "TgUser",
        secondary=approved_user_models,
        back_populates="approved_user_models",
        overlaps="users"
    )


class GPTPrompt(Base):
    __tablename__ = 'gpt_prompts'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(28), nullable=False)

    en_prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    ru_prompt_text: Mapped[str] = mapped_column(Text, nullable=False)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    consumer: Mapped[ConsumerEnum] = mapped_column(
        ChoiceType(ConsumerEnum, impl=String()),
        nullable=False,
        default=ConsumerEnum.FAST_CHAT,
    )
