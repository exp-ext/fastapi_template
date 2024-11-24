import uuid
from typing import List, Optional, Tuple

from fastapi import Depends, Request, UploadFile
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (AuthenticationBackend,
                                          BearerTransport, JWTStrategy)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import UserAlreadyExists
from sqlalchemy import UUID, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.conf import logger, settings
from src.crud import image_dao
from src.db.deps import get_user_db
from src.models import Image, TgGroup, User
from src.schemas.user_schema import UserCreate

logger = logger.getChild(__name__)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY
    image_path = "users"

    def __init__(self, user_db: SQLAlchemyUserDatabase, user: Optional[User] = None):
        super().__init__(user_db)
        self.user = user

    @property
    def db_session(self) -> AsyncSession:
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

    async def get_or_create_by_tg_id(self, tg_id: int, **kwargs) -> Tuple[User, bool]:
        user = await self.get_by_tg_id(tg_id=tg_id)

        if user:
            return user, False
        try:
            data = {'tg_id': tg_id, **kwargs}

            validated_data = UserCreate(**data).model_dump()
            password = validated_data.pop('password')
            await self.validate_password(password, validated_data)
            validated_data["hashed_password"] = self.password_helper.hash(password)

            user = await self.user_db.create(validated_data)
            return user, True
        except UserAlreadyExists:
            user = await self.get_by_tg_id(tg_id)
            return user, False

    async def get_by_tg_id(self, *, tg_id: int) -> User | None:
        query = select(User).where(User.tg_id == tg_id)
        result = await self.db_session.execute(query)
        return result.scalars().one_or_none()

    async def get_all_users(self) -> list[User]:
        result = await self.db_session.execute(select(User))
        return result.scalars().all()

    async def get_all_tg_users(self) -> list[User]:
        query = select(User).where(User.tg_id.isnot(None))
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def search_users_by_query(self, *, query: str) -> list[User]:
        try:
            query_as_int = int(query)
            search_condition = cast(User.tg_id, String).ilike(f"%{query_as_int}%")
        except ValueError:
            search_condition = User.tg_username.ilike(f"%{query}%")

        result = await self.db_session.execute(select(User).where(search_condition))
        return result.scalars().all()

    async def is_admin_by_tg_id(self, tg_id: int) -> bool:
        query = select(User.is_superuser).where(User.tg_id == tg_id)
        result = await self.db_session.execute(query)
        is_superuser = result.scalar_one_or_none()
        return bool(is_superuser)

    async def get_with_prefetch_related(self, id: UUID | None = None, tg_id: int | None = None, prefetch_related: List | None = None) -> User | None:
        if id:
            query = select(User).where(User.id == id)
        else:
            query = select(User).where(User.tg_id == tg_id)
        load_options = [selectinload(getattr(User, attr)) for attr in prefetch_related]
        query = query.options(*load_options)
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def add_group(self, *, user: User, group: TgGroup,) -> User | None:
        user.tg_groups.append(group)
        await self.db_session.commit()
        await self.db_session.refresh(user, ["groups"])
        return user


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


async def get_user_manager_without_db_session(db_session: AsyncSession) -> UserManager:
    user_db = SQLAlchemyUserDatabase(db_session, User)
    return UserManager(user_db)


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


async def authenticate_websocket_user(token: str, user_db: AsyncSession) -> Optional[User]:
    """
    Аутентификация пользователя по токену для WebSocket.
    """
    jwt_strategy = JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)
    try:
        user_manager = UserManager(user_db)
        payload = await jwt_strategy.read_token(token, user_manager)

        user_id = payload.id
        if user_id is None:
            return None

        result = await user_db.session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if user:
            return user
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to authenticate user: {e}")
        return None
