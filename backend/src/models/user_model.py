from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base_model import Base
from src.models.interim_tables import user_image_association


class User(SQLAlchemyBaseUserTable, Base):
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)

    image_files = relationship("Image", secondary=user_image_association, back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, first_name={self.first_name}, last_name={self.last_name})>"
