from fastapi import HTTPException, UploadFile
from sqlalchemy import UUID
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.conf import media_storage
from src.crud.base_crud import GenericCRUD
from src.models.image_model import Image
from src.schemas.image_schema import ImageCreate, ImageDAOResponse, ImageUpdate
from src.utils.s3_utils import S3Manager


class ImageDAO(GenericCRUD[Image, ImageCreate, ImageUpdate]):

    async def get(self, *, id: UUID | str, db_session: AsyncSession | None = None) -> ImageDAOResponse | None:
        db_obj = await super().get(id=id, db_session=db_session)
        url = db_obj.get_url()
        return ImageDAOResponse(image=db_obj, url=url)

    async def create_with_file(self, *, file: UploadFile, is_main: bool, path: str = "", db_session: AsyncSession | None = None) -> Image | None:
        s3_manager = S3Manager(storage=media_storage)
        file_key = await s3_manager.put_object(file, path)
        db_obj = self.model(file=file_key, is_main=is_main)
        db_session.add(db_obj)
        await db_session.commit()
        return db_obj

    async def update_file(self, *, id: UUID, file: UploadFile, is_main: bool, path: str = "", db_session: AsyncSession | None = None) -> Image | None:
        db_obj = await super().get(id=id, db_session=db_session)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Object not found")

        s3_manager = S3Manager(storage=media_storage)
        new_key = await s3_manager.update_object(file, db_obj.file, path)

        db_obj.file = new_key
        db_obj.is_main = is_main
        db_session.add(db_obj)
        await db_session.commit()
        await db_session.refresh(db_obj)
        return db_obj

    async def delete(self, *, id: UUID, db_session: AsyncSession | None = None) -> Image | None:
        s3_manager = S3Manager(storage=media_storage)
        db_obj = await super().get(id=id, db_session=db_session)
        if not db_obj:
            return

        if db_obj.file:
            await s3_manager.delete_object(db_obj.file)

        await db_session.delete(db_obj)
        await db_session.commit()

    async def create_without_file(self, *, file_name: str, is_main: bool, path: str = "", db_session: AsyncSession | None = None) -> ImageDAOResponse | None:
        s3_manager = S3Manager(storage=media_storage)
        url, file_key = await s3_manager.generate_upload_url(file_name, path=path)
        db_obj = self.model(file=file_key, is_main=is_main)
        db_session.add(db_obj)
        await db_session.commit()
        return ImageDAOResponse(image=db_obj, url=url)

    async def update_without_file(self, *, id: UUID, file_name: str, is_main: bool, path: str = "", db_session: AsyncSession | None = None) -> ImageDAOResponse | None:
        db_obj = await super().get(id=id, db_session=db_session)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Object not found")
        s3_manager = S3Manager(storage=media_storage)
        url, file_key = await s3_manager.generate_update_url(file_name, db_obj.file, path=path)
        db_obj.file = file_key
        db_obj.is_main = is_main
        db_session.add(db_obj)
        await db_session.commit()
        await db_session.refresh(db_obj)
        return ImageDAOResponse(image=db_obj, url=url)


image_dao = ImageDAO(Image)
