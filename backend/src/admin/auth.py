import contextlib
from typing import Optional

from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from sqladmin.authentication import AuthenticationBackend
from src.conf import settings
from src.crud.user_crud import UserManager, get_user_db, get_jwt_strategy
from src.db.deps import get_async_session
from src.models import User


class AdminAuth(AuthenticationBackend):
    def __init__(self):
        super().__init__(settings.SECRET_KEY)
        self.jwt_strategy = get_jwt_strategy()

    @contextlib.asynccontextmanager
    async def get_user_manager(self):
        async for session in get_async_session():
            async for user_db in get_user_db(session):
                yield UserManager(user_db)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        async with self.get_user_manager() as user_manager:
            credentials = OAuth2PasswordRequestForm(username=email, password=password)
            user = await user_manager.authenticate(credentials)
            if user and user.is_active:
                token = await self.jwt_strategy.write_token(user)
                return user, token
            return None, None

    async def login(self, request: Request):
        form = await request.form()
        username = form["username"]
        password = form["password"]

        user, token = await self.authenticate_user(username, password)
        if user and user.is_superuser:
            request.session.update({"access_token": token})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("access_token")
        if not token:
            return False
        try:
            async with self.get_user_manager() as user_manager:
                user = await self.jwt_strategy.read_token(token, user_manager)
                if user is None:
                    return False
                if user and user.is_superuser:
                    return True
                else:
                    return False
        except Exception:
            return False
