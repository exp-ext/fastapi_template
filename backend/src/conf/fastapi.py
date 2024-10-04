import base64
import os
import secrets
from enum import Enum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class ModeEnum(str, Enum):
    development = "development"
    production = "production"
    testing = "testing"


class Settings(BaseSettings):
    MODE: str = os.environ.get("MODE")

    REDIS_HOST: str = os.environ.get("REDIS_HOST")
    REDIS_PORT: str = os.environ.get("REDIS_PORT")
    REDIS_PASSWORD: str = os.environ.get("REDIS_PASSWORD")
    DB_POOL_SIZE: int = 83
    WEB_CONCURRENCY: int = 9
    POOL_SIZE: int = max(DB_POOL_SIZE // WEB_CONCURRENCY, 5)

    RABBITMQ_HOST: str = os.getenv('RABBITMQ_HOST')
    RABBITMQ_PORT: str = os.getenv('RABBITMQ_PORT')
    RABBITMQ_DEFAULT_USER: str = os.getenv('RABBITMQ_DEFAULT_USER')
    RABBITMQ_DEFAULT_PASS: str = os.getenv('RABBITMQ_DEFAULT_PASS')

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: int = os.getenv("POSTGRES_PORT")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    DATABASE_CELERY_NAME: str = "celery_schedule_jobs"

    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_DOMAIN: str = os.getenv("MINIO_DOMAIN")
    MINIO_REGION_NAME: str = os.getenv("MINIO_REGION_NAME")
    MINIO_MEDIA_BUCKET: str = os.getenv("MINIO_MEDIA_BUCKET")
    MINIO_STATIC_BUCKET: str = os.getenv("MINIO_STATIC_BUCKET")
    MINIO_DATABASE_BUCKET: str = os.getenv("MINIO_DATABASE_BUCKET")
    MINIO_USE_SSL: bool = int(os.getenv("MINIO_USE_SSL"))

    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ENCRYPT_KEY: str = os.getenv("ENCRYPT_KEY", base64.urlsafe_b64encode(os.urandom(32)).decode())

    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN")
    SECRET_BOT_URL: str = os.getenv("SECRET_BOT_URL")
    DOMAIN: str = os.getenv("DOMAIN")

    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    @field_validator("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", mode="after")
    def assemble_celery_urls(cls, v: str | None, info: FieldValidationInfo):
        if all(info.data.get(attr) for attr in ["RABBITMQ_DEFAULT_USER", "RABBITMQ_DEFAULT_PASS", "RABBITMQ_HOST", "RABBITMQ_PORT"]):
            url = (
                f"amqp://{info.data['RABBITMQ_DEFAULT_USER']}:"
                f"{info.data['RABBITMQ_DEFAULT_PASS']}@"
                f"{info.data['RABBITMQ_HOST']}:"
                f"{info.data['RABBITMQ_PORT']}//"
            )
            if info.field_name == "CELERY_BROKER_URL":
                return url
            elif info.field_name == "CELERY_RESULT_BACKEND":
                return url
        return v

    ASYNC_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("ASYNC_DATABASE_URI", mode="after")
    def assemble_async_db_connection(cls, v: str | None, info: FieldValidationInfo) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_HOST"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["POSTGRES_DB"],
                )
        return v

    SYNC_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("SYNC_DATABASE_URI", mode="after")
    def assemble_sync_db_connection(cls, v: str | None, info: FieldValidationInfo) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+psycopg2",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_HOST"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["POSTGRES_DB"],
                )
        return v

    SYNC_CELERY_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("SYNC_CELERY_DATABASE_URI", mode="after")
    def assemble_celery_db_connection(
        cls, v: str | None, info: FieldValidationInfo
    ) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="db+postgresql",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_HOST"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["DATABASE_CELERY_NAME"],
                )
        return v

    SYNC_CELERY_BEAT_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("SYNC_CELERY_BEAT_DATABASE_URI", mode="after")
    def assemble_celery_beat_db_connection(
        cls, v: str | None, info: FieldValidationInfo
    ) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+psycopg2",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_HOST"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["DATABASE_CELERY_NAME"],
                )
        return v

    ASYNC_CELERY_BEAT_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("ASYNC_CELERY_BEAT_DATABASE_URI", mode="after")
    def assemble_async_celery_beat_db_connection(
        cls, v: str | None, info: FieldValidationInfo
    ) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_HOST"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["DATABASE_CELERY_NAME"],
                )
        return v

    BACKEND_CORS_ORIGINS: str | list[AnyHttpUrl] = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost")

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    project_root: Path = Path(__file__).parent.parent.resolve()
    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=os.path.expanduser("~/.env")
    )


settings = Settings()
