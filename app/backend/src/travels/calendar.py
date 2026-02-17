import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from icalendar import Calendar, Event
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_admin_user
from ..database import get_db
from ..models import AppSetting, PersonalEvent, Trip, TripDestination
from .events import EVENT_CATEGORIES

CALENDAR_TOKEN_KEY = "calendar_feed_token"

router = APIRouter()


def _get_token(db: Session) -> str | None:
    """Get the calendar feed token from the database."""
    setting = db.get(AppSetting, CALENDAR_TOKEN_KEY)
    return setting.value if setting else None


def _build_calendar(db: Session) -> bytes:
    """Build ICS calendar with all trips and personal events."""
    cal = Calendar()
    cal.add("prodid", "-//rembish.org//Calendar Feed//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", "rembish.org travels")

    # Add trips
    trips = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations).joinedload(TripDestination.tcc_destination),
            joinedload(Trip.cities),
        )
        .order_by(Trip.start_date)
        .all()
    )

    for trip in trips:
        event = Event()

        # Summary: destination names or "Trip"
        dest_names = [td.tcc_destination.name for td in trip.destinations]
        summary = ", ".join(dest_names) if dest_names else "Trip"
        event.add("summary", summary)

        # All-day events use DATE type
        event.add("dtstart", trip.start_date)
        # DTEND is exclusive in iCal — add 1 day
        end = trip.end_date or trip.start_date
        event.add("dtend", end + timedelta(days=1))

        # Description
        parts: list[str] = []
        if trip.trip_type != "regular":
            parts.append(f"Type: {trip.trip_type}")
        city_names = [c.name for c in sorted(trip.cities, key=lambda c: c.order)]
        if city_names:
            parts.append(f"Cities: {', '.join(city_names)}")
        if trip.description:
            parts.append(trip.description)
        if parts:
            event.add("description", "\n".join(parts))

        event.add("uid", f"trip-{trip.id}@rembish.org")
        cal.add_component(event)

    # Add personal events
    events = db.query(PersonalEvent).order_by(PersonalEvent.event_date).all()

    for pe in events:
        event = Event()

        emoji = EVENT_CATEGORIES.get(pe.category, "\U0001f4cc")
        event.add("summary", f"{emoji} {pe.title}")

        event.add("dtstart", pe.event_date)
        end = pe.end_date or pe.event_date
        event.add("dtend", end + timedelta(days=1))

        if pe.note:
            event.add("description", pe.note)

        event.add("uid", f"event-{pe.id}@rembish.org")
        cal.add_component(event)

    result: bytes = cal.to_ical()
    return result


@router.get("/calendar.ics")
def get_calendar_feed(
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> Response:
    """Public ICS calendar feed. Authenticated by token query parameter."""
    stored_token = _get_token(db)
    if not stored_token:
        raise HTTPException(status_code=404, detail="Calendar feed not configured")
    if token != stored_token:
        raise HTTPException(status_code=403, detail="Invalid token")

    ics_data = _build_calendar(db)
    return Response(
        content=ics_data,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=calendar.ics"},
    )


@router.get("/calendar/feed-token")
def get_feed_token(
    admin: object = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, str | None]:
    """Get current calendar feed token (admin only). Frontend builds the URL."""
    return {"token": _get_token(db)}


@router.post("/calendar/regenerate-token")
def regenerate_token(
    admin: object = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Generate a new calendar feed token. Old links stop working immediately."""
    new_token = str(uuid.uuid4())

    setting = db.get(AppSetting, CALENDAR_TOKEN_KEY)
    if setting:
        setting.value = new_token
    else:
        db.add(AppSetting(key=CALENDAR_TOKEN_KEY, value=new_token))

    db.commit()

    return {"token": new_token}
