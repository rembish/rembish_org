from fastapi import APIRouter

from .calendar import router as calendar_router
from .car_rentals import router as car_rentals_router
from .data import router as data_router
from .events import router as events_router
from .flights import router as flights_router
from .location import router as location_router
from .photos import router as photos_router
from .stats import router as stats_router
from .transport_bookings import router as transport_bookings_router
from .trips import router as trips_router
from .upload import router as upload_router

router = APIRouter(prefix="/v1/travels", tags=["travels"])
router.include_router(calendar_router)
router.include_router(car_rentals_router)
router.include_router(data_router)
router.include_router(events_router)
router.include_router(flights_router)
router.include_router(location_router)
router.include_router(photos_router)
router.include_router(stats_router)
router.include_router(transport_bookings_router)
router.include_router(upload_router)
router.include_router(trips_router)
