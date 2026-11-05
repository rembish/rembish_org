"""Tests for AI-extracted date validation against trip windows."""

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.extraction import ExtractedFlight, FlightExtractionResult, trip_date_context
from src.models import Trip
from src.travels.date_check import check_dates

START = date(2026, 11, 13)
END = date(2026, 11, 22)


def test_date_inside_trip_is_untouched() -> None:
    values = {"dep": "2026-11-13", "arr": None}
    fixed, warning = check_dates(values, START, END)
    assert fixed == values
    assert warning is None


def test_slack_around_trip_is_accepted() -> None:
    # Evening departure the day before / overnight arrival the day after
    fixed, warning = check_dates({"dep": "2026-11-12", "arr": "2026-11-23"}, START, END)
    assert warning is None
    assert fixed["dep"] == "2026-11-12"


def test_wrong_year_is_corrected_with_all_fields() -> None:
    fixed, warning = check_dates({"dep": "2024-11-21", "arr": "2024-11-22"}, START, END)
    assert fixed == {"dep": "2026-11-21", "arr": "2026-11-22"}
    assert warning is not None and "2024 to 2026" in warning


def test_datetime_values_keep_their_time() -> None:
    fixed, warning = check_dates(
        {"pickup": "2024-11-14 10:30", "dropoff": "2024-11-21 18:00"}, START, END
    )
    assert fixed == {"pickup": "2026-11-14 10:30", "dropoff": "2026-11-21 18:00"}
    assert warning is not None


def test_year_end_trip_picks_matching_year() -> None:
    fixed, warning = check_dates({"dep": "2025-01-02"}, date(2026, 12, 23), date(2027, 1, 4))
    assert fixed["dep"] == "2027-01-02"
    assert warning is not None


def test_unfixable_date_is_flagged_not_changed() -> None:
    fixed, warning = check_dates({"dep": "2026-06-01"}, START, END)
    assert fixed["dep"] == "2026-06-01"
    assert warning is not None and "outside the trip" in warning


def test_open_ended_trip_uses_start_date() -> None:
    _, warning = check_dates({"dep": "2024-12-24"}, date(2008, 11, 23), None)
    assert warning is not None and "outside the trip" in warning


def test_empty_and_garbage_values() -> None:
    assert check_dates({"dep": None, "arr": None}, START, END) == (
        {"dep": None, "arr": None},
        None,
    )
    _, warning = check_dates({"dep": "13NOV"}, START, END)
    assert warning is not None


def test_prompt_context_mentions_trip_window() -> None:
    assert trip_date_context(None, None) == ""
    ctx = trip_date_context(START, END)
    assert "2026-11-13" in ctx and "2026-11-22" in ctx


@patch("src.travels.flights.extract_flight_data")
def test_extract_flights_corrects_year(
    mock_extract: MagicMock, admin_client: TestClient, db_session: Session
) -> None:
    trip = Trip(start_date=START, end_date=END, trip_type="regular")
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    mock_extract.return_value = FlightExtractionResult(
        flights=[
            ExtractedFlight(
                flight_date="2024-11-21",
                arrival_date="2024-11-22",
                flight_number="BA2152",
                departure_iata="BGI",
                arrival_iata="LGW",
            ),
            ExtractedFlight(flight_date="2026-11-14", flight_number="BA2153"),
        ]
    )

    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/flights/extract",
        files={"file": ("ticket.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert res.status_code == 200
    flights = res.json()["flights"]
    assert flights[0]["flight_date"] == "2026-11-21"
    assert flights[0]["arrival_date"] == "2026-11-22"
    assert "2024 to 2026" in flights[0]["date_warning"]
    assert flights[1]["date_warning"] is None

    _, kwargs = mock_extract.call_args
    assert kwargs["trip_start"] == START
    assert kwargs["trip_end"] == END


@patch("src.travels.accommodations.extract_accommodation_data")
def test_extract_accommodation_shifts_payment_date(
    mock_extract: MagicMock, admin_client: TestClient, db_session: Session
) -> None:
    from src.extraction import AccommodationExtractionResult, ExtractedAccommodation

    trip = Trip(start_date=START, end_date=END, trip_type="regular")
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    mock_extract.return_value = AccommodationExtractionResult(
        accommodation=ExtractedAccommodation(
            property_name="Sea View",
            checkin_date="2024-11-14",
            checkout_date="2024-11-21",
            payment_date="2024-10-01",
        )
    )
    res = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/accommodations/extract",
        files={"file": ("booking.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert res.status_code == 200
    acc = res.json()["accommodation"]
    assert acc["checkin_date"] == "2026-11-14"
    assert acc["checkout_date"] == "2026-11-21"
    assert acc["payment_date"] == "2026-10-01"
    assert acc["date_warning"]
