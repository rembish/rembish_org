from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.session import get_admin_user
from ..database import get_db
from ..models import PersonalEvent
from .models import (
    EventCreateRequest,
    EventData,
    EventsResponse,
    EventUpdateRequest,
)

router = APIRouter(dependencies=[Depends(get_admin_user)])

EVENT_CATEGORIES: dict[str, str] = {
    "medical": "\U0001f3e5",
    "car": "\U0001f697",
    "event": "\U0001f389",
    "admin": "\U0001f4cb",
    "social": "\U0001f465",
    "home": "\U0001f527",
    "pet": "\U0001f431",
    "photo": "\U0001f4f7",
    "boardgames": "\U0001f3b2",
    "other": "\U0001f4cc",
}


def _event_to_data(event: PersonalEvent) -> EventData:
    return EventData(
        id=event.id,
        event_date=event.event_date.isoformat(),
        end_date=event.end_date.isoformat() if event.end_date else None,
        title=event.title,
        note=event.note,
        category=event.category,
        category_emoji=EVENT_CATEGORIES.get(event.category, "\U0001f4cc"),
    )


@router.get("/events")
def list_events(db: Session = Depends(get_db)) -> EventsResponse:
    events = db.query(PersonalEvent).order_by(PersonalEvent.event_date).all()
    return EventsResponse(
        events=[_event_to_data(e) for e in events],
        total=len(events),
        categories=EVENT_CATEGORIES,
    )


@router.get("/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)) -> EventData:
    event = db.get(PersonalEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_to_data(event)


@router.post("/events", status_code=201)
def create_event(data: EventCreateRequest, db: Session = Depends(get_db)) -> EventData:
    if data.category not in EVENT_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category '{data.category}'. "
            f"Must be one of: {', '.join(EVENT_CATEGORIES)}",
        )

    event = PersonalEvent(
        event_date=date.fromisoformat(data.event_date),
        end_date=date.fromisoformat(data.end_date) if data.end_date else None,
        title=data.title,
        note=data.note,
        category=data.category,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _event_to_data(event)


@router.put("/events/{event_id}")
def update_event(
    event_id: int, data: EventUpdateRequest, db: Session = Depends(get_db)
) -> EventData:
    event = db.get(PersonalEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if data.category is not None and data.category not in EVENT_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category '{data.category}'. "
            f"Must be one of: {', '.join(EVENT_CATEGORIES)}",
        )

    if data.event_date is not None:
        event.event_date = date.fromisoformat(data.event_date)
    if data.end_date is not None:
        event.end_date = date.fromisoformat(data.end_date)
    if data.title is not None:
        event.title = data.title
    if data.note is not None:
        event.note = data.note
    if data.category is not None:
        event.category = data.category

    db.commit()
    db.refresh(event)
    return _event_to_data(event)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> None:
    event = db.get(PersonalEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
