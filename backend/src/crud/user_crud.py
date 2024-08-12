import uuid
from typing import Optional

from fastapi import Depends, Request, UploadFile
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (AuthenticationBackend,
                                          BearerTransport, JWTStrategy)
from fastapi_users.db import SQLAlchemyUserDatabase
from src.conf import logger, settings
from src.crud import image_dao
from src.db.deps import get_user_db
from src.models import Image, User

logger = logger.getChild(__name__)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY
    image_path = "users"

    def __init__(self, user_db: SQLAlchemyUserDatabase, user: Optional[User] = None):
        super().__init__(user_db)
        self.user = user

    @property
    def db_session(self):
        return self.user_db.session

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.debug(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.debug(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.debug(f"Verification requested for user {user.id}. Verification token: {token}")

    async def save_user_image(self, file: UploadFile, is_main: bool) -> Image:
        image = await image_dao.create_with_file(
            file=file, is_main=is_main, model_instance=self.user, path=self.image_path, db_session=self.db_session
        )
        return image

    async def update_user_image(self, image_id: uuid.UUID, file: UploadFile, is_main: bool) -> Image:
        image = await image_dao.update_file(id=image_id, file=file, is_main=is_main, model_instance=self.user, path=self.image_path, db_session=self.db_session)
        return image

    async def delete_user_image(self, image_id: uuid.UUID) -> None:
        await image_dao.delete(
            id=image_id, model_instance=self.user, related_model=Image, db_session=self.db_session
        )

    async def save_user_image_with_upload_url(self, file_name: str, is_main: bool) -> str:
        image_dao_resp = await image_dao.create_without_file(
            is_main=is_main, file_name=file_name, model_instance=self.user, path=self.image_path, db_session=self.db_session
        )
        return image_dao_resp

    async def update_user_image_with_upload_url(self, image_id: uuid.UUID, file_name: str, is_main: bool) -> str:
        image_dao_resp = await image_dao.update_without_file(
            id=image_id, file_name=file_name, is_main=is_main, model_instance=self.user, path=self.image_path, db_session=self.db_session
        )
        return image_dao_resp


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)


async def get_current_active_user_and_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
    user: User = Depends(current_active_user)
):
    yield UserManager(user_db, user)
