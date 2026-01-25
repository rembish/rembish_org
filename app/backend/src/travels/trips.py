from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user
from ..database import get_db
from ..models import Trip, TripDestination, TripParticipant, User
from .models import TripCityData, TripData, TripDestinationData, TripParticipantData, TripsResponse

router = APIRouter()


@router.get("/trips", response_model=TripsResponse)
def get_trips(
    admin: Annotated[User, Depends(get_admin_user)],
    db: Session = Depends(get_db),
) -> TripsResponse:
    """Get all trips (admin only)."""
    trips = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination),
            joinedload(Trip.participants).joinedload(TripParticipant.user),
            joinedload(Trip.cities),
        )
        .order_by(Trip.start_date.desc())
        .all()
    )

    trips_data = [
        TripData(
            id=trip.id,
            start_date=trip.start_date.isoformat(),
            end_date=trip.end_date.isoformat() if trip.end_date else None,
            trip_type=trip.trip_type,
            flights_count=trip.flights_count,
            working_days=trip.working_days,
            rental_car=trip.rental_car,
            description=trip.description,
            destinations=[
                TripDestinationData(
                    name=td.tcc_destination.name,
                    is_partial=td.is_partial,
                )
                for td in trip.destinations
            ],
            cities=[
                TripCityData(
                    name=city.name,
                    is_partial=city.is_partial,
                )
                for city in sorted(trip.cities, key=lambda c: c.order)
            ],
            participants=[
                TripParticipantData(
                    id=tp.user.id,
                    name=tp.user.name,
                    nickname=tp.user.nickname,
                    picture=tp.user.picture,
                )
                for tp in trip.participants
            ],
            other_participants_count=trip.other_participants_count,
        )
        for trip in trips
    ]

    return TripsResponse(trips=trips_data, total=len(trips_data))
