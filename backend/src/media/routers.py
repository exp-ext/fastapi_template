from typing import List

from fastapi import APIRouter, Depends, Form, Query
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from src.crud import current_active_user, image_dao
from src.db.deps import get_async_session
from src.models.user_model import User
from src.tasks.image_tasks import process_image_task
from starlette import status

media_router = APIRouter()


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


@media_router.post("/images/treatment/", status_code=status.HTTP_200_OK)
async def create_task_image_treatment(
    image_id: UUID4 = Form(...),
    _: User = Depends(current_active_user),
):
    await process_image_task.kiq(image_id=image_id)
    return 'Done'
