from typing import Any, Generic, Type, TypeVar
from uuid import UUID

from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import exc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from src.models.base_model import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseModel)
T = TypeVar("T", bound=Base)


class GenericCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    db: AsyncSession

    def __init__(self, model: type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: Model model class
        * `schema`: Pydantic model (schema) class
        """
        self.model = model
        self.db = db

    def get_db(self) -> Type[AsyncSession]:
        return self.db

    async def get(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> ModelType | None:
        db_session = db_session or self.db.session
        query = select(self.model).where(self.model.id == id)
        result = await db_session.execute(query)
        return result.scalars().one_or_none()

    async def get_by_ids(self, *, list_ids: list[UUID | str], db_session: AsyncSession | None = None,) -> list[ModelType] | None:
        db_session = db_session or self.db.session
        result = await db_session.execute(
            select(self.model).where(self.model.id.in_(list_ids))
        )
        return result.scalars().all()

    async def get_count(self, db_session: AsyncSession | None = None) -> ModelType | None:
        db_session = db_session or self.db.session
        result = await db_session.execute(
            select(func.count()).select_from(select(self.model).subquery())
        )
        return result.scalar()

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, query: Select[ModelType] | None = None, db_session: AsyncSession | None = None,
    ) -> list[ModelType]:
        db_session = db_session or self.db.session
        if query is None:
            query = select(self.model).offset(skip).limit(limit).order_by(self.model.id)
        result = await db_session.execute(query)
        return result.scalars().all()

    async def get_multi_paginated(
        self, *, params: Params | None = Params(), query: T | Select[T] | None = None, db_session: AsyncSession | None = None,
    ) -> Page[ModelType]:
        db_session = db_session or self.db.session
        if query is None:
            query = select(self.model)

        output = await paginate(db_session, query, params)
        return output

    async def create(
        self, *, obj_in: CreateSchemaType | ModelType, created_by_id: UUID | str | None = None, db_session: AsyncSession | None = None,
    ) -> ModelType:
        db_session = db_session or self.db.session

        if not isinstance(obj_in, self.model):
            db_obj = self.model(**obj_in.model_dump())
        else:
            db_obj = obj_in

        if created_by_id and hasattr(db_obj, 'created_by_id'):
            db_obj.id = created_by_id

        try:
            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        await db_session.refresh(db_obj)
        return db_obj

    async def update(
        self, *, obj_current: ModelType, obj_new: UpdateSchemaType | dict[str, Any] | ModelType, db_session: AsyncSession | None = None,
    ) -> ModelType:
        db_session = db_session or self.db.session

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
        self, *, id: UUID | str, db_session: AsyncSession | None = None
    ) -> ModelType:
        db_session = db_session or self.db.session
        result = await db_session.execute(select(self.model).where(self.model.id == id))
        obj = result.scalars().one()
        await db_session.delete(obj)
        await db_session.commit()
        return obj
