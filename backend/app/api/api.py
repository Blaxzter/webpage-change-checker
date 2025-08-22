from fastapi import APIRouter

from app.api.routes import test, users, websites

api_router = APIRouter()

api_router.include_router(test.router)
api_router.include_router(users.router)
api_router.include_router(websites.router)
