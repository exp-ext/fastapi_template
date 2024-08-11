import io
import os
from typing import List, Type

import filetype
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from src.conf.s3_client import S3AsyncClient


class S3Manager:

    def __init__(self, storage: Type[S3AsyncClient]):
        self.storage = storage

    def _prepare_path(self, path: str) -> str:
        """
        Подготавливает путь, добавляя '/' в конец, если его нет.

        Аргументы:
        - path (`str`): Путь к объекту в S3.

        Возвращает:
        - `str`: Подготовленный путь с завершающим '/'.
        """
        if path and not path.endswith('/'):
            path += '/'
        return path

    async def _read_file(self, file: UploadFile) -> tuple[bytes, str]:
        """
        Читает содержимое файла и возвращает его содержимое и имя файла.

        Аргументы:
        - file (`UploadFile`): Загружаемый файл.

        Возвращает:
        - `tuple[bytes, str]`: Кортеж, содержащий байты файла и его имя.
        """
        file_content = await file.read()
        file_name = file.filename
        return file_content, file_name

    async def _generate_unique_key(self, s3_client, file_name: str) -> str:
        """
        Генерирует уникальный ключ для файла в S3, добавляя суффиксы в случае коллизии имен.

        Аргументы:
        - s3_client: Клиент S3, используемый для взаимодействия с сервисом.
        - file_name (`str`): Предлагаемое имя файла.

        Возвращает:
        - `str`: Уникальный ключ для файла в S3.
        """
        base_name, extension = os.path.splitext(file_name)
        key = file_name
        counter = 1
        while True:
            try:
                await s3_client.head_object(Bucket=self.storage.bucket_name, Key=key)
                key = f"{base_name}_{counter}{extension}"
                counter += 1
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    break
                else:
                    raise
        return key

    def _convert_to_webp(self, file_content: bytes) -> tuple[bytes, str]:
        """
        Преобразует изображение в формат WEBP и возвращает содержимое файла и MIME-тип.

        Аргументы:
        - file_content (`bytes`): Содержимое изображения в байтах.

        Возвращает:
        - `tuple[bytes, str]`: Кортеж, содержащий преобразованное содержимое и MIME-тип.
        """
        try:
            image = Image.open(io.BytesIO(file_content))
            image.verify()
            output = io.BytesIO()
            image.save(output, format="WEBP")
            return output.getvalue(), "image/webp"
        except UnidentifiedImageError as e:
            raise HTTPException(status_code=400, detail="Invalid image file") from e

    async def _check_and_delete_object(self, s3_client, key: str) -> None:
        """
        Проверяет существование объекта в S3 и удаляет его, если он существует.

        Аргументы:
        - s3_client: Клиент S3, используемый для взаимодействия с сервисом.
        - key (`str`): Ключ (имя) объекта в S3.

        Исключения:
        - HTTPException: Возникает при ошибке проверки или удаления объекта в S3, кроме случая, когда объект не найден.
        """
        try:
            await s3_client.head_object(Bucket=self.storage.bucket_name, Key=key)
            await self.delete_object(key)
        except ClientError as e:
            if e.response['Error']['Code'] != '404':
                raise HTTPException(status_code=500, detail="Error checking or deleting existing file in S3") from e

    async def get_url(self, key: str, expiration: int = 3600) -> str:
        """
        Генерирует и возвращает URL для доступа к объекту в S3. Если объект публичный,
        возвращает прямой URL, иначе создает подписанный URL с ограниченным сроком действия.

        Аргументы:
        - key (`str`): Ключ (имя) объекта в S3.
        - expiration (`int`, optional): Срок действия подписанного URL в секундах. По умолчанию 3600.

        Возвращает:
        - `str`: URL для доступа к объекту в S3.
        """
        async with self.storage.client as s3_client:
            protocol = "https" if self.storage.use_ssl else "http"
            if hasattr(self.storage, 'custom_domain') and self.storage.custom_domain:
                return f"{protocol}://{self.storage.custom_domain}/{key}"
            if self.storage.default_acl == 'public-read':
                return f"{protocol}://{self.storage.endpoint_domain}/{self.storage.bucket_name}/{key}"
            try:
                url = await s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.storage.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
                return url
            except ClientError as e:
                raise HTTPException(status_code=500, detail="Error generating presigned URL") from e

    async def list_objects(self, path: str = "", file_type: str = "all") -> List[str]:
        """
        Возвращает список объектов в S3 бакете, фильтруя их по типу файла (изображения или все).

        Аргументы:
        - path (`str`, optional): Путь в бакете для поиска объектов. По умолчанию "".
        - file_type (`str`, optional): Тип файлов для фильтрации ("images", "non_images" или "all"). По умолчанию "all".

        Возвращает:
        - `List[str]`: Список ключей (имен) объектов, удовлетворяющих условиям фильтрации.

        Исключения:
            HTTPException: Возникает при ошибке подключения к S3 или других критических ошибках.
        """
        async with self.storage.client as s3_client:
            try:
                prefix = self._prepare_path(path)

                response = await s3_client.list_objects_v2(
                    Bucket=self.storage.bucket_name,
                    Prefix=prefix
                )

                if 'Contents' not in response:
                    return []

                def is_image(key: str) -> bool:
                    return key.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))

                def filter_key(obj):
                    if file_type == "images":
                        return is_image(obj['Key'])
                    elif file_type == "non_images":
                        return not is_image(obj['Key'])
                    else:
                        return True

                return [obj['Key'] for obj in response['Contents'] if filter_key(obj)]

            except ClientError as e:
                raise HTTPException(status_code=500, detail="Error connecting to S3 or retrieving objects") from e

    async def put_object(self, file: UploadFile, path: str = "") -> str:
        """
        Асинхронно загружает файл в S3 бакет и возвращает ключ (имя) объекта в хранилище.

        Аргументы:
        - file (`UploadFile`): Загружаемый файл.
        - path (`str`, optional): Путь в бакете для размещения файла. По умолчанию "".

        Возвращает:
        - `str`: Ключ (имя) объекта в S3.
        """
        async with self.storage.client as s3_client:
            file_content, file_name = await self._read_file(file)
            path = self._prepare_path(path)

            kind = filetype.guess(file_content)
            is_image = kind is not None and kind.mime.startswith("image")

            if is_image:
                file_content, content_type = self._convert_to_webp(file_content)
                file_name = os.path.splitext(file_name)[0] + ".webp"
            else:
                content_type = kind.mime if kind else 'application/octet-stream'

            key = await self._generate_unique_key(s3_client, path + file_name)

            try:
                await s3_client.put_object(
                    Bucket=self.storage.bucket_name,
                    Key=key,
                    Body=file_content,
                    ContentType=content_type,
                    ACL=self.storage.default_acl
                )
            except ClientError as e:
                raise HTTPException(status_code=500, detail="Error uploading file to S3") from e

            return key

    async def update_object(self, file: UploadFile, old_key: str, path: str = "") -> str:
        """
        Обновляет существующий объект в S3, удаляя старый и загружая новый файл.

        Аргументы:
        - file (`UploadFile`): Новый файл для загрузки.
        - old_key (`str`): Старый ключ объекта для удаления.
        - path (`str`, optional): Путь в бакете для размещения файла. По умолчанию "".

        Возвращает:
        - `str`: Ключ (имя) нового объекта в S3.
        """
        async with self.storage.client as s3_client:
            await self._check_and_delete_object(s3_client, old_key)

            path = self._prepare_path(path)
            new_key = await self.put_object(file, path)
            return new_key

    async def generate_upload_url(self, file_name: str, expiration: int = 3600, path: str = "") -> str:
        """
        Генерирует и возвращает предписанный URL для загрузки файла в S3.

        Аргументы:
        - file_name (`str`): Ключ объекта в S3.
        - expiration (`int`, optional): Срок действия предписанного URL в секундах. По умолчанию 3600.
        - path (`str`): Путь (папка) к объекту в S3, по которому файл будет загружен.

        Возвращает:
        - `str`: Предписанный URL для загрузки файла в S3.

        Исключения:
        - HTTPException: Возникает при ошибке генерации предписанного URL.
        """
        async with self.storage.client as s3_client:
            path = self._prepare_path(path)
            key = await self._generate_unique_key(s3_client, path + file_name)
            try:
                url = await s3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': self.storage.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
                return url, key
            except ClientError as e:
                raise HTTPException(status_code=500, detail="Error generating presigned upload URL") from e

    async def generate_update_url(self, file_name: str, old_key: str, expiration: int = 3600, path: str = "") -> str:
        """
        Генерирует и возвращает предписанный URL для обновления файла в S3.

        Аргументы:
        - file_name (`str`): Ключ (имя) объекта в S3.
        - old_key (`str`): Старый ключ объекта для удаления.
        - expiration (`int`, optional): Срок действия предписанного URL в секундах. По умолчанию 3600.
        - path (`str`, optional): Путь (папка) к объекту в S3, по которому файл будет загружен.

        Возвращает:
        - `str`: Предписанный URL для загрузки файла в S3.
        """
        async with self.storage.client as s3_client:
            await self._check_and_delete_object(s3_client, old_key)

            path = self._prepare_path(path)
            key = await self._generate_unique_key(s3_client, path + file_name)
            try:
                url = await s3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': self.storage.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
                return url, key
            except ClientError as e:
                raise HTTPException(status_code=500, detail="Error generating presigned upload URL") from e

    async def delete_object(self, key: str) -> None:
        """
        Удаляет объект из S3 по заданному ключу.

        Аргументы:
        - key (`str`): Ключ объекта в S3.

        Исключения:
        - HTTPException: Возникает при ошибке удаления объекта в S3, кроме случаев, когда объект не найден.
        """
        async with self.storage.client as s3_client:
            try:
                await s3_client.delete_object(Bucket=self.storage.bucket_name, Key=key)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code != 'NoSuchKey':
                    raise HTTPException(status_code=500, detail="Error deleting file from S3") from e
