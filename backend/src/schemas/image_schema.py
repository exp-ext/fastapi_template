import uuid

from pydantic import BaseModel, HttpUrl

from models import Image


class ImageCreate(BaseModel):
    file: str
    is_main: bool


class ImageUpdate(ImageCreate):
    id: uuid.UUID


class UploadImageResponse(BaseModel):
    id: uuid.UUID
    is_main: bool

    class Config:
        from_attributes = True


class ImageDAOResponse(BaseModel):
    image: Image
    url: HttpUrl


class UploadUrlImageResponse(BaseModel):
    image: ImageDAOResponse
    front_key: str
