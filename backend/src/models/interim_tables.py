from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.dialects.postgresql import UUID as UUIDType
from src.models.base_model import Base

user_image_association = Table(
    "user_image_association",
    Base.metadata,
    Column("user_id", UUIDType(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("image_id", UUIDType(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), primary_key=True),
)

user_tg_group_association = Table(
    "user_tg_group_association",
    Base.metadata,
    Column("user_id", UUIDType(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("tg_groups.id"), primary_key=True),
)

approved_user_models = Table(
    "approved_user_models",
    Base.metadata,
    Column("user_id", UUIDType(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("ai_model_id", UUIDType(as_uuid=True), ForeignKey("ai_models.id"), primary_key=True),
)
