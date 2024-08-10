from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as UUIDType
from src.models.base_model import Base

user_media_association = Table(
    'user_image_association', Base.metadata,
    Column('user_id', UUIDType(as_uuid=True), ForeignKey('user.id'), primary_key=True),
    Column('image_id', UUIDType(as_uuid=True), ForeignKey('image.id'), primary_key=True)
)
