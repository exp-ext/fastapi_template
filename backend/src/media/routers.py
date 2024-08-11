from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import UUID4
from src.conf import media_storage
from src.crud import current_active_user
from src.models.user_model import User
from src.utils.s3_utils import S3Manager
from starlette import status
from src.crud import image_dao

media_router = APIRouter()


@media_router.get("/all-images", status_code=status.HTTP_200_OK)
async def get_images(user: User = Depends(current_active_user)):
    s3_manager = S3Manager(storage=media_storage)
    file_path = "users"
    images_path_parts = await s3_manager.list_objects(path=file_path, file_type="all")
    return JSONResponse({"urls": images_path_parts})


@media_router.get("/images/{image_id}", status_code=status.HTTP_200_OK)
async def get_image(image_id: UUID4):
    image = await image_dao.get(id=image_id)
    return image
