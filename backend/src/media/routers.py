from typing import List

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from src.crud import current_active_user, image_dao
from src.db.deps import get_async_session
from src.models.user_model import User
from src.utils.s3_utils import S3Manager
from starlette import status

media_router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@media_router.get("/all-images/", status_code=status.HTTP_200_OK)
async def get_all_images(
    storage: str = Form(...),
    user: User = Depends(current_active_user)
):
    s3_manager = S3Manager(storage=storage)
    file_path = "users"
    images_path_parts = await s3_manager.list_objects(path=file_path, file_type="all")
    return JSONResponse({"urls": images_path_parts})


@media_router.get("/images/{image_id}", status_code=status.HTTP_200_OK)
async def get_image(image_id: UUID4):
    image = await image_dao.get(id=image_id)
    return image


@media_router.get("/images/", status_code=status.HTTP_200_OK)
async def get_images(
    image_ids: List[UUID4] = Query(...),
    db_session: AsyncSession = Depends(get_async_session)
):
    images = await image_dao.get_by_ids(list_ids=image_ids, db_session=db_session)
    return images


@media_router.get("/upload-photo/")
async def upload_photo(request: Request):
    return templates.TemplateResponse("media/upload_photo.html", {"request": request})
