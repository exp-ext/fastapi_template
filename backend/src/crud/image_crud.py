import asyncio
from typing import Type

from fastapi import HTTPException, UploadFile
from sqlalchemy import UUID, Table, select, update
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import aliased
from src.crud.base_crud import GenericCRUD
from src.models.base_model import Base
from src.models.image_model import Image
from src.schemas.image_schema import ImageCreate, ImageDAOResponse, ImageUpdate


class ImageDAO(GenericCRUD[Image, ImageCreate, ImageUpdate]):

    async def _reset_is_main(self, model_name: str, model_instance: Base, association_table_name: str, db_session: AsyncSession):
        """Сбрасывает значение is_main для всех изображений, связанных с моделью."""
        association_table = Table(association_table_name, Base.metadata, autoload_with=db_session.bind)
        image_alias = aliased(Image)
        stmt = (
            select(image_alias.id)
            .select_from(association_table)
            .join(image_alias, association_table.c["image_id"] == image_alias.id)
            .where(association_table.c[f"{model_name}_id"] == model_instance.id)
            .where(image_alias.is_main == True)  # noqa: E712
        )
        result = await db_session.execute(stmt)
        image_ids = [row[0] for row in result.fetchall()]
        if image_ids:
            stmt = (
                update(Image)
                .where(Image.id.in_(image_ids))
                .values(is_main=False)
            )
            await db_session.execute(stmt)
            await db_session.commit()

    async def _get_image_url(self, db_obj: Image) -> ImageDAOResponse:
        """Получает url к экземпляру Image."""
        url = await db_obj.storage.generate_url(db_obj.file)
        return ImageDAOResponse(image=db_obj, url=url)

    async def get(
        self, *, id: UUID | str, scheme: bool = True, db_session: AsyncSession | None = None
    ) -> ImageDAOResponse | None:
        db_obj = await super().get(id=id, db_session=db_session)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Object not found")
        if scheme:
            image_with_url = await self._get_image_url(db_obj)
            return image_with_url
        url = await db_obj.storage.generate_url(db_obj.file)
        return db_obj, url

    async def get_by_ids(self, *, list_ids: list[UUID | str], db_session: AsyncSession | None = None,) -> list[Image] | None:
        db_objs = await super().get_by_ids(list_ids=list_ids, db_session=db_session)
        if not db_objs:
            raise HTTPException(status_code=404, detail="No objects found")

        tasks = [self._get_image_url(db_obj) for db_obj in db_objs]
        images_with_urls = await asyncio.gather(*tasks)
        return images_with_urls

    async def create_with_file(
        self, *, file: UploadFile, is_main: bool, model_instance: Type[Base], path: str = "", db_session: AsyncSession | None = None
    ) -> Image | None:
        model_name, association_table_name = await self._check_association_table(
            model_instance=model_instance,
            related_model=self.model,
            db_session=db_session
        )

        if is_main:
            await self._reset_is_main(model_name, model_instance, association_table_name, db_session)

        db_obj = self.model(is_main=is_main)
        db_obj.file = await db_obj.storage.put_object(file, path)
        db_session.add(db_obj)
        await db_session.flush()

        association_table = Table(association_table_name, Base.metadata, autoload_with=db_session.bind)
        stmt = association_table.insert().values(**{f"{model_name}_id": model_instance.id, "image_id": db_obj.id})
        await db_session.execute(stmt)
        await db_session.commit()
        await db_session.refresh(db_obj)

        return db_obj

    async def update_file(self, *, id: UUID, file: UploadFile, is_main: bool, model_instance: Type[Base], path: str = "", db_session: AsyncSession | None = None) -> Image | None:
        model_name, association_table_name = await self._check_association_table(
            model_instance=model_instance,
            related_model=self.model,
            db_session=db_session
        )

        db_obj = await super().get(id=id, db_session=db_session)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Object not found")

        db_obj.file = await db_obj.storage.update_object(file, db_obj.file, path)
        db_obj.is_main = is_main

        if is_main:
            await self._reset_is_main(model_name, model_instance, association_table_name, db_session)

        await db_session.commit()
        await db_session.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: UUID, model_instance: Type[Base], related_model: Type[Base], db_session: AsyncSession | None = None) -> None:
        _, association_table_name = await self._check_association_table(
            model_instance=model_instance,
            related_model=related_model,
            db_session=db_session
        )

        db_obj = await super().get(id=id, db_session=db_session)
        if not db_obj:
            return

        if db_obj.file:
            await db_obj.storage.delete_object(db_obj.file)

        association_table = Table(association_table_name, Base.metadata, autoload_with=db_session.bind)
        stmt = association_table.delete().where(association_table.c.image_id == id)
        await db_session.execute(stmt)

        await db_session.delete(db_obj)
        await db_session.commit()

    async def create_without_file(
        self, *, file_name: str, is_main: bool, model_instance: Type[Base], path: str = "", db_session: AsyncSession | None = None
    ) -> ImageDAOResponse | None:
        model_name, association_table_name = await self._check_association_table(
            model_instance=model_instance,
            related_model=self.model,
            db_session=db_session
        )

        if is_main:
            await self._reset_is_main(model_name, model_instance, association_table_name, db_session)

        db_obj = self.model(is_main=is_main)
        url, db_obj.file = await db_obj.storage.generate_upload_url(file_name, path=path)
        db_session.add(db_obj)
        await db_session.flush()

        association_table = Table(association_table_name, Base.metadata, autoload_with=db_session.bind)
        stmt = association_table.insert().values(**{f"{model_name}_id": model_instance.id, "image_id": db_obj.id})
        await db_session.execute(stmt)
        await db_session.commit()
        await db_session.refresh(db_obj)

        return ImageDAOResponse(image=db_obj, url=url)

    async def update_without_file(self, *, id: UUID, file_name: str, is_main: bool, model_instance: Type[Base], path: str = "", db_session: AsyncSession | None = None) -> ImageDAOResponse | None:
        model_name, association_table_name = await self._check_association_table(
            model_instance=model_instance,
            related_model=self.model,
            db_session=db_session
        )
        db_obj = await super().get(id=id, db_session=db_session)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Object not found")

        if is_main:
            await self._reset_is_main(model_name, model_instance, association_table_name, db_session)

        url, db_obj.file = await db_obj.storage.generate_update_url(file_name, db_obj.file, path=path)
        db_obj.is_main = is_main
        await db_session.commit()
        await db_session.refresh(db_obj)
        return ImageDAOResponse(image=db_obj, url=url)


image_dao = ImageDAO(Image)
