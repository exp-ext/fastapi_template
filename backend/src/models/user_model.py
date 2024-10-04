from typing import TYPE_CHECKING, List, Optional

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_model import Base
from src.models.interim_tables import (user_image_association,
                                       user_tg_group_association)

if TYPE_CHECKING:
    from src.models import Image, TgGroup


class User(SQLAlchemyBaseUserTable, Base):
    __tablename__ = "users"

    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    tg_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tg_users.id"), nullable=True, unique=True)
    tg_user: Mapped[Optional["TgUser"]] = relationship(
        "TgUser",
        back_populates="user",
        uselist=False,
        cascade="all, delete"
    )
    image_files: Mapped[List["Image"]] = relationship(
        "Image",
        secondary=user_image_association,
        back_populates="users",
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<User(id={self.id}, first_name={self.first_name}, last_name={self.last_name})>"


class TgUser(Base):
    __tablename__ = "tg_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_blocked_bot: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="tg_user",
        uselist=False
    )
    groups: Mapped[List["TgGroup"]] = relationship(
        "TgGroup",
        secondary=user_tg_group_association,
        back_populates="users",
        cascade="all, delete",
        lazy='raise'
    )

    def __repr__(self):
        return f"<TgUser(id={self.id}, first_name={self.first_name}, last_name={self.last_name})>"
