import uuid

from pydantic import BaseModel, HttpUrl


class ImageSchema(BaseModel):
    id: uuid.UUID
    file: str
    is_main: bool

    class Config:
        from_attributes = True


class ImageCreate(BaseModel):
    file: str
    is_main: bool


class ImageUpdate(ImageCreate):
    id: uuid.UUID


class UploadImageResponse(BaseModel):
    id: uuid.UUID
    is_main: bool


class ImageDAOResponse(BaseModel):
    image: ImageSchema
    url: HttpUrl


class UploadUrlImageResponse(BaseModel):
    image: ImageDAOResponse
    front_key: str
