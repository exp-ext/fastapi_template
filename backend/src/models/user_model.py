from typing import TYPE_CHECKING, List, Optional

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_model import Base
from src.models.interim_tables import (approved_user_models,
                                       user_image_association,
                                       user_tg_group_association)

if TYPE_CHECKING:
    from src.models import (AIModels, AITransactions, Image, TgGroup,
                            UserAIModel)


class User(SQLAlchemyBaseUserTable, Base):
    __tablename__ = "users"

    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    tg_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, index=True)
    tg_username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_blocked_bot: Mapped[bool] = mapped_column(Boolean, default=False)

    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    image_files: Mapped[List["Image"]] = relationship(
        "Image",
        secondary=user_image_association,
        back_populates="users",
        cascade="all, delete",
        passive_deletes=True,
    )

    approved_user_models: Mapped[List["AIModels"]] = relationship(
        "AIModels",
        secondary=approved_user_models,
        back_populates="users",
        cascade="save-update, merge",
    )

    active_model: Mapped[Optional["UserAIModel"]] = relationship(
        "UserAIModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    tg_groups: Mapped[List["TgGroup"]] = relationship(
        "TgGroup",
        secondary=user_tg_group_association,
        back_populates="users",
        cascade="save-update, merge",
    )

    ai_transactions: Mapped[List["AITransactions"]] = relationship("AITransactions", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, first_name={self.first_name}, last_name={self.last_name})>"

    def get_full_name(self) -> str:
        """
        Возвращает полное имя пользователя, объединяя first_name и last_name.
        Если ни first_name, ни last_name не заданы, возвращает tg_username.
        """
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full_name if full_name else self.tg_username
