from fastapi import APIRouter

from .cosplay import router as cosplay_router
from .fixers import router as fixers_router
from .instagram import router as instagram_router
from .memes import router as memes_router
from .users import router as users_router
from .vault import router as vault_router

router = APIRouter(prefix="/v1/admin", tags=["admin"])
router.include_router(cosplay_router)
router.include_router(fixers_router)
router.include_router(memes_router)
router.include_router(users_router)
router.include_router(instagram_router)
router.include_router(vault_router)
