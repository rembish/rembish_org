from fastapi import APIRouter

from .instagram import router as instagram_router
from .users import router as users_router

router = APIRouter(prefix="/v1/admin", tags=["admin"])
router.include_router(users_router)
router.include_router(instagram_router)
