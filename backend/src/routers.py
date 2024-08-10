from fastapi import APIRouter
from src.auth.routers import auth_router, users_router
from src.users.routers import media_router

main_router = APIRouter()
main_router.include_router(auth_router, prefix="/auth", tags=["auth"])
main_router.include_router(users_router, prefix="/users", tags=["users"])
main_router.include_router(media_router, prefix="/users-account", tags=["users-account"])
