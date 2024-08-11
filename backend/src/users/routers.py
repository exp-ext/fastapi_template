from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import UUID4
from src.crud import UserManager, get_current_active_user_and_manager
from src.schemas.image_schema import (ImageDAOResponse, UploadImageResponse,
                                      UploadUrlImageResponse)
from starlette import status

account_router = APIRouter()


@account_router.post("/upload-image", response_model=UploadImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_user_image(
    file: UploadFile = File(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image = await user_manager.save_user_image(file=file, is_main=is_main)
    return UploadImageResponse(id=image.id, file=image.file, is_main=image.is_main)


@account_router.put("/update-image/{image_id}", response_model=UploadImageResponse, status_code=status.HTTP_200_OK)
async def update_user_image(
    image_id: UUID4,
    file: UploadFile = File(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image = await user_manager.update_user_image(image_id=image_id, file=file, is_main=is_main)
    return UploadImageResponse(id=image.id, file=image.file, is_main=image.is_main)


@account_router.delete("/delete-image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_image(
    image_id: UUID4,
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    await user_manager.delete_user_image(image_id=image_id)
    return {"detail": "Image deleted successfully"}


@account_router.post("/upload-url-image", response_model=UploadUrlImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_user_image_with_url(
    file_name: str = Form(...),
    is_main: bool = Form(...),
    front_key: str = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image_dao_resp = await user_manager.save_user_image_with_upload_url(file_name, is_main=is_main)
    return UploadUrlImageResponse(image=image_dao_resp, front_key=front_key)


@account_router.post("/update-url-image/{image_id}", response_model=ImageDAOResponse, status_code=status.HTTP_201_CREATED)
async def update_user_image_with_url(
    image_id: UUID4,
    file_name: str = Form(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image_dao_resp = await user_manager.update_user_image_with_upload_url(image_id, file_name, is_main)
    return image_dao_resp
