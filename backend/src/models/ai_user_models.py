import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_model import Base

if TYPE_CHECKING:
    from src.models import AIModels, GPTPrompt, User


class UserAIModel(Base):
    __tablename__ = 'user_ai_models'

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    time_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True)
    user: Mapped["User"] = relationship("User", back_populates="active_model")

    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_models.id", ondelete="CASCADE"), nullable=True)
    model: Mapped["AIModels"] = relationship("AIModels", foreign_keys=[model_id])

    prompt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("gpt_prompts.id", ondelete="CASCADE"), nullable=True)
    prompt: Mapped["GPTPrompt"] = relationship("GPTPrompt", foreign_keys=[prompt_id])
