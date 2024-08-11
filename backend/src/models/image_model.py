from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.conf import media_storage
from src.models.base_model import Base
from src.models.interim_tables import user_media_association
from src.utils.s3_utils import S3Manager


class Image(Base):
    __tablename__ = "image"

    file: Mapped[str] = mapped_column(String, nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    users = relationship("User", secondary=user_media_association, back_populates="image_files")

    def __repr__(self):
        return f"<Media(id={self.id}, file={self.file}, is_main={self.is_main})>"

    async def get_url(self) -> str:
        """Возвращает фактический URL файла, хранящегося в S3."""
        if not self.file:
            return ""
        s3_manager = S3Manager(storage=media_storage)
        file_url = await s3_manager.get_url(self.file)
        return file_url
