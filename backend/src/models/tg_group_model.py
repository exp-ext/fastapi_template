from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_model import Base

from . import user_tg_group_association

if TYPE_CHECKING:
    from src.models import User


class TgGroup(Base):
    __tablename__ = "tg_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=True)
    link: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_tg_group_association,
        back_populates="tg_groups",
    )

    def __repr__(self):
        return f"<TgGroup(id={self.id}, chat_id={self.chat_id}, title={self.title})>"
