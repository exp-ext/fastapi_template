from typing import Type

from sqlalchemy.types import String, TypeDecorator
from src.conf import S3StorageManager


class FilePath(TypeDecorator):
    impl = String

    def __init__(self, storage: Type[S3StorageManager], *args, **kwargs):
        self._storage = storage
        super().__init__(*args, **kwargs)

    @property
    def storage(self):
        return self._storage

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value

    async def async_process_result_value(self, value):
        if value is not None:
            return await self.storage.generate_url(value)
        return value
