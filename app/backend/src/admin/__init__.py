from fastapi import APIRouter

from .fixers import router as fixers_router
from .instagram import router as instagram_router
from .users import router as users_router
from .vault import router as vault_router

router = APIRouter(prefix="/v1/admin", tags=["admin"])
router.include_router(fixers_router)
router.include_router(users_router)
router.include_router(instagram_router)
router.include_router(vault_router)
