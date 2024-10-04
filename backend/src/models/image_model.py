from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.conf import media_storage
from src.models.base_model import Base
from src.models.interim_tables import user_image_association
from src.models.sql_decorator import FilePath

if TYPE_CHECKING:
    from src.conf import S3StorageManager
    from src.models import User


class Image(Base):
    __tablename__ = "images"
    _file_storage = media_storage

    file: Mapped[str] = mapped_column(FilePath(_file_storage), nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_image_association,
        back_populates="image_files"
    )

    def __repr__(self):
        return f"<Media(id={self.id}, file={self.file}, is_main={self.is_main})>"

    @property
    def storage(self) -> "S3StorageManager":
        """Возвращает объект storage, чтобы использовать его методы напрямую."""
        return self._file_storage
