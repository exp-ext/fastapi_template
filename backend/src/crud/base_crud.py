from typing import Any, Generic, List, Type, TypeVar
from uuid import UUID

from fastapi import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import exc, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from src.conf import logger
from src.models.base_model import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseModel)
T = TypeVar("T", bound=Base)
logger = logger.getChild(__name__)


class GenericCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> ModelType | None:
        query = select(self.model).where(self.model.id == id)
        result = await db_session.execute(query)
        return result.scalars().one_or_none()

    async def get_by_ids(self, *, list_ids: list[UUID | str], db_session: AsyncSession | None = None,) -> list[ModelType] | None:
        result = await db_session.execute(
            select(self.model).where(self.model.id.in_(list_ids))
        )
        return result.scalars().all()

    async def get_count(self, db_session: AsyncSession | None = None) -> ModelType | None:
        result = await db_session.execute(
            select(func.count()).select_from(select(self.model).subquery())
        )
        return result.scalar()

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, query: Select[ModelType] | None = None, db_session: AsyncSession | None = None,
    ) -> list[ModelType]:
        if query is None:
            query = select(self.model).offset(skip).limit(limit).order_by(self.model.id)
        result = await db_session.execute(query)
        return result.scalars().all()

    async def get_multi_paginated(
        self, *, params: Params | None = Params(), query: T | Select[T] | None = None, db_session: AsyncSession | None = None,
    ) -> Page[ModelType]:
        if query is None:
            query = select(self.model)

        output = await paginate(db_session, query, params)
        return output

    async def create(
        self, *, obj_in: CreateSchemaType | ModelType | None = None, created_by_id: UUID | int | None = None, relationship_refresh: List = [], db_session: AsyncSession | None = None,
    ) -> ModelType:

        if obj_in is None:
            if created_by_id is None:
                raise ValueError("Either obj_in or created_by_id must be provided")
            db_obj = self.model(id=created_by_id)
        elif not isinstance(obj_in, self.model):
            db_obj = self.model(**obj_in.model_dump())
        else:
            db_obj = obj_in

        if created_by_id:
            db_obj.id = created_by_id

        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        await db_session.refresh(db_obj, relationship_refresh)
        return db_obj

    async def update(
        self, *, obj_current: ModelType, obj_new: UpdateSchemaType | dict[str, Any] | ModelType, db_session: AsyncSession | None = None,
    ) -> ModelType:

        if isinstance(obj_new, dict):
            update_data = obj_new
        else:
            update_data = obj_new.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(obj_current, field, update_data[field])

        db_session.add(obj_current)
        await db_session.commit()
        await db_session.refresh(obj_current)
        return obj_current

    async def remove(
        self, *, id: UUID | int, db_session: AsyncSession | None = None
    ) -> ModelType:
        result = await db_session.execute(select(self.model).where(self.model.id == id))
        obj = result.scalars().one_or_none()
        if not obj:
            return None
        await db_session.delete(obj)
        await db_session.commit()
        return obj

    def _get_table_names(self, connection):
        inspector = inspect(connection)
        return inspector.get_table_names()

    async def _check_association_table(self, model_instance: Type[Base], related_model: Type[Base], db_session: AsyncSession) -> tuple[str, str]:
        """
        Проверяет наличие промежуточной таблицы между моделями.
        Если таблицы нет, логирует ошибку и генерирует общее исключение для клиента.
        """
        model_name = model_instance.__class__.__name__.lower()
        related_model_name = related_model.__name__.lower()
        association_table_name = f"{model_name}_{related_model_name}_association"

        conn = await db_session.connection()
        table_names = await conn.run_sync(self._get_table_names)

        if association_table_name not in table_names:
            logger.error(
                f"You need to create an intermediate table to link {model_name} to {related_model_name}.\n\n"
                f"Add to {model_instance.__class__.__name__} model:\n"
                f"{model_name}s = relationship(\"{related_model.__name__}\", secondary=\"{association_table_name}\", back_populates=\"{related_model_name}_files\")\n\n"
                f"To {related_model.__name__} model:\n"
                f"{related_model_name}_files = relationship(\"{model_instance.__class__.__name__}\", secondary=\"{association_table_name}\", back_populates=\"{model_name}s\")\n\n"
                f"Create an intermediate table:\n"
                f"{association_table_name} = Table(\n"
                f"    '{association_table_name}', Base.metadata,\n"
                f"    Column('{model_name}_id', UUID(as_uuid=True), ForeignKey('{model_instance.__tablename__}.id'), primary_key=True),\n"
                f"    Column('{related_model_name}_id', UUID(as_uuid=True), ForeignKey('{related_model.__tablename__}.id'), primary_key=True)\n"
            )
            raise HTTPException(
                status_code=500,
                detail="Server Error: Association table is missing."
            )

        return model_name, association_table_name
