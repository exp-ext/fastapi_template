from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import UUID4
from src.conf import media_storage
from src.crud import (UserManager, current_active_user,
                      get_current_active_user_and_manager)
from src.models.user_model import User
from src.schemas.image_schema import (ImageDAOResponse, UploadImageResponse,
                                      UploadUrlImageResponse)
from src.utils.s3_utils import S3Manager
from starlette import status

media_router = APIRouter()


@media_router.get("/all-images", status_code=status.HTTP_200_OK)
async def get_images(user: User = Depends(current_active_user)):
    s3_manager = S3Manager(storage=media_storage)
    file_path = "users"
    images_path_parts = await s3_manager.list_objects(path=file_path, file_type="all")
    return JSONResponse({"urls": images_path_parts})


@media_router.post("/upload-image", response_model=UploadImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_user_image(
    file: UploadFile = File(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image = await user_manager.save_user_image(file=file, is_main=is_main)
    return UploadImageResponse(id=image.id, file=image.file, is_main=image.is_main)


@media_router.put("/update-image/{image_id}", response_model=UploadImageResponse, status_code=status.HTTP_200_OK)
async def update_user_image(
    image_id: UUID4,
    file: UploadFile = File(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image = await user_manager.update_user_image(image_id=image_id, file=file, is_main=is_main)
    return UploadImageResponse(id=image.id, file=image.file, is_main=image.is_main)


@media_router.delete("/delete-image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_image(
    image_id: UUID4,
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    await user_manager.delete_user_image(image_id=image_id)
    return {"detail": "Image deleted successfully"}


@media_router.post("/upload-url-image", response_model=UploadUrlImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_user_image_with_url(
    file_name: str = Form(...),
    is_main: bool = Form(...),
    front_key: str = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image_dao_resp = await user_manager.save_user_image_with_upload_url(file_name, is_main=is_main)
    return UploadUrlImageResponse(image=image_dao_resp, front_key=front_key)


@media_router.post("/update-url-image/{image_id}", response_model=ImageDAOResponse, status_code=status.HTTP_201_CREATED)
async def update_user_image_with_url(
    image_id: UUID4,
    file_name: str = Form(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image_dao_resp = await user_manager.update_user_image_with_upload_url(image_id, file_name, is_main)
    return image_dao_resp
