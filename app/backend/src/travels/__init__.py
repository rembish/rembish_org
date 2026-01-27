from fastapi import APIRouter

from .data import router as data_router
from .location import router as location_router
from .stats import router as stats_router
from .trips import router as trips_router
from .upload import router as upload_router

router = APIRouter(prefix="/v1/travels", tags=["travels"])
router.include_router(data_router)
router.include_router(location_router)
router.include_router(stats_router)
router.include_router(upload_router)
router.include_router(trips_router)
