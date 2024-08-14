from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from src.auth.routers import auth_router, users_router
from src.media.routers import media_router
from src.users.routers import account_router

templates = Jinja2Templates(directory="src/templates")
main_router = APIRouter()
main_router.include_router(auth_router, prefix="/auth", tags=["auth"])
main_router.include_router(users_router, prefix="/users", tags=["users"])
main_router.include_router(account_router, prefix="/users-account", tags=["users-account"])
main_router.include_router(media_router, prefix="/assets", tags=["assets"])


@main_router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
