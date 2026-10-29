"""Tests for GPS logger track processing and the trip tracks API.

All tracks here are synthetic — never put real logger data in this repo.
"""

import gzip
from datetime import UTC, date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import GpsTrack, GpsTrackLeg, TCCDestination, Trip, TripDestination, UNCountry
from src.travels.gps_processing import parse_csv, process_points, simplify

HEADER = "INDEX,TAG,DATE,TIME,LATITUDE N/S,LONGITUDE E/W,HEIGHT,SPEED,HEADING\n"
START = datetime(2030, 3, 10, 8, 0, 0, tzinfo=UTC)
# One degree of latitude is about 111 km; these steps give the speeds in comments.
WALK_STEP = 0.0000125  # ~1.4 m/s, 5 km/h
DRIVE_STEP = 0.00015  # ~16.7 m/s, 60 km/h


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.counter = 0

    def save(self, user_id: int, filename: str, content: bytes, content_type: str) -> str:
        self.counter += 1
        key = f"{user_id}/{self.counter}.gz"
        self.files[key] = content
        return key

    def read(self, key: str) -> bytes | None:
        return self.files.get(key)

    def delete(self, key: str) -> bool:
        return self.files.pop(key, None) is not None


def _row(i: int, tag: str, t: datetime, lat: float, lon: float, speed: float) -> str:
    ns = f"{abs(lat):.7f}{'N' if lat >= 0 else 'S'}"
    ew = f"{abs(lon):.7f}{'E' if lon >= 0 else 'W'}"
    return f"{i},{tag},{t:%y%m%d},{t:%H%M%S},{ns},{ew},100,{speed},0\n"


def _synthetic_day(start: datetime = START) -> bytes:
    """10 min walk, 20 min standing gap, 15 min drive, 9 min dropout moving 3 km, 10 min walk."""
    rows: list[str] = []
    t, lat, lon = start, 10.0, 20.0

    def emit(n: int, step: float, speed: float, tag: str = "T") -> None:
        nonlocal t, lat
        for k in range(n):
            rows.append(_row(len(rows) + 1, tag if k == 0 else "T", t, lat, lon, speed))
            t += timedelta(seconds=1)
            lat += step

    emit(600, WALK_STEP, 5.0)
    t += timedelta(minutes=20)  # asleep at a café: same place
    emit(900, DRIVE_STEP, 60.0, tag="G")
    t += timedelta(minutes=9)  # tunnel: no fix while moving 3 km
    lat += 0.027
    emit(600, WALK_STEP, 5.0, tag="G")
    return (HEADER + "".join(rows)).encode()


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------


def test_parse_csv_reads_hemispheres_and_utc() -> None:
    content = (HEADER + _row(1, "T", START, -33.5, -70.25, 3.0)).encode()
    [p] = parse_csv(content)
    assert (p.lat, p.lon) == (-33.5, -70.25)
    assert p.t == START


def test_parse_csv_rejects_other_csv() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        parse_csv(b"name,value\na,1\n")


def test_parse_csv_skips_malformed_and_glitches() -> None:
    rows = [
        _row(1, "T", START, 10.0, 20.0, 1.0),
        "2,T,garbage,row,,,,,\n",
        _row(3, "T", START + timedelta(seconds=1), 11.0, 20.0, 1.0),  # 111 km in 1 s
        _row(4, "T", START + timedelta(seconds=2), 10.00001, 20.0, 1.0),
    ]
    points = parse_csv((HEADER + "".join(rows)).encode())
    assert [p.lat for p in points] == [10.0, 10.00001]


def test_process_points_finds_walk_stop_drive_gap_walk() -> None:
    track = process_points(parse_csv(_synthetic_day()))
    assert [leg.mode for leg in track.legs] == ["foot", "stop", "vehicle", "gap", "foot"]
    walk, stop, drive, gap, _ = track.legs
    assert walk.distance_km == pytest.approx(0.83, abs=0.05)
    assert drive.distance_km == pytest.approx(15.0, abs=0.5)
    assert gap.distance_km == pytest.approx(3.0, abs=0.1)
    assert (stop.ended_at - stop.started_at) == timedelta(minutes=20, seconds=1)
    assert stop.lines == []
    assert track.wake_count == 2
    # Gap distance is a straight line without a fix; it does not count as travelled.
    assert track.distance_km == pytest.approx(
        sum(leg.distance_km for leg in track.legs if leg.mode != "gap")
    )


def test_short_walk_in_traffic_is_absorbed_into_drive() -> None:
    rows: list[str] = []
    t, lat = START, 10.0
    for speed, n in ((60.0, 300), (2.0, 120), (60.0, 300)):
        step = DRIVE_STEP if speed > 10 else WALK_STEP / 2
        for _ in range(n):
            rows.append(_row(len(rows) + 1, "T", t, lat, 20.0, speed))
            t += timedelta(seconds=1)
            lat += step
    track = process_points(parse_csv((HEADER + "".join(rows)).encode()))
    assert [leg.mode for leg in track.legs] == ["vehicle"]


def test_simplify_keeps_corners_drops_straight_points() -> None:
    line = [[0.0, float(x)] for x in range(10)] + [[float(y), 9.0] for y in range(1, 10)]
    assert simplify(line, 1e-6) == [[0.0, 0.0], [0.0, 9.0], [9.0, 9.0]]


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@pytest.fixture()
def storage() -> FakeStorage:
    fake = FakeStorage()
    with patch("src.travels.gps_tracks.get_vault_storage", return_value=fake):
        yield fake


def _trip(db: Session, tz: str | None = "America/Santiago") -> Trip:
    trip = Trip(start_date=date(2030, 3, 9), end_date=date(2030, 3, 12), trip_type="regular")
    db.add(trip)
    db.flush()
    if tz:
        un = UNCountry(
            name="Testland",
            iso_alpha2="TL",
            iso_alpha3="TLD",
            iso_numeric="999",
            continent="Testica",
            map_region_codes="999",
            timezone=tz,
        )
        db.add(un)
        db.flush()
        tcc = TCCDestination(
            name="Testland", tcc_region="Testica", tcc_index=999, un_country_id=un.id
        )
        db.add(tcc)
        db.flush()
        db.add(TripDestination(trip_id=trip.id, tcc_destination_id=tcc.id))
    db.commit()
    return trip


def _upload(
    client: TestClient, trip_id: int, content: bytes, name: str = "10080000.CSV", **form: str
) -> dict:
    r = client.post(
        f"/api/v1/travels/trips/{trip_id}/gps-tracks/upload",
        files=[("files", (name, content, "text/csv"))],
        data=form,
    )
    assert r.status_code == 200, r.text
    return r.json()["results"][0]


def test_upload_stores_gzipped_raw_and_legs(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    content = _synthetic_day()
    result = _upload(admin_client, trip.id, content)
    assert result["status"] == "created"

    track = db_session.get(GpsTrack, result["track_id"])
    assert track is not None
    assert gzip.decompress(storage.files[track.raw_path]) == content
    # 08:00 UTC is 05:00 in Santiago (UTC-3 in March), still the same date
    assert track.timezone == "America/Santiago"
    assert track.local_date == date(2030, 3, 10)
    assert len(track.legs) == 5

    r = admin_client.get(f"/api/v1/travels/trips/{trip.id}/gps-tracks")
    body = r.json()
    assert body["default_timezone"] == "America/Santiago"
    [day] = body["tracks"]
    assert day["started_at"] == "2030-03-10T08:00:00Z"
    assert [leg["mode"] for leg in day["legs"]] == ["foot", "stop", "vehicle", "gap", "foot"]


def test_local_date_follows_timezone(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session, tz=None)
    late = datetime(2030, 3, 10, 22, 30, tzinfo=UTC)
    result = _upload(admin_client, trip.id, _synthetic_day(late), timezone="Asia/Tokyo")
    track = db_session.get(GpsTrack, result["track_id"])
    assert track is not None and track.local_date == date(2030, 3, 11)


def test_reupload_replaces_and_removes_old_raw(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    first = _upload(admin_client, trip.id, _synthetic_day())
    second = _upload(admin_client, trip.id, _synthetic_day())
    assert second["status"] == "replaced"
    assert second["track_id"] == first["track_id"]
    assert len(storage.files) == 1
    assert db_session.query(GpsTrack).count() == 1
    assert db_session.query(GpsTrackLeg).count() == 5


def test_upload_rejects_bad_files_individually(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    r = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/gps-tracks/upload",
        files=[
            ("files", ("notes.txt", b"hello", "text/plain")),
            ("files", ("other.csv", b"a,b\n1,2\n", "text/csv")),
            ("files", ("10080000.CSV", _synthetic_day(), "text/csv")),
        ],
    )
    statuses = [res["status"] for res in r.json()["results"]]
    assert statuses == ["error", "error", "created"]


def test_upload_refuses_day_from_another_trip(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    first, second = _trip(db_session), _trip(db_session, tz=None)
    _upload(admin_client, first.id, _synthetic_day())
    result = _upload(admin_client, second.id, _synthetic_day())
    assert result["status"] == "error"
    assert f"trip #{first.id}" in result["detail"]


def test_upload_rejects_unknown_timezone(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    r = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/gps-tracks/upload",
        files=[("files", ("a.csv", _synthetic_day(), "text/csv"))],
        data={"timezone": "Mars/Olympus"},
    )
    assert r.status_code == 400


def test_reprocess_changes_timezone(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    track_id = _upload(admin_client, trip.id, _synthetic_day())["track_id"]
    r = admin_client.post(
        f"/api/v1/travels/gps-tracks/{track_id}/reprocess", json={"timezone": "Pacific/Auckland"}
    )
    assert r.status_code == 200
    assert r.json()["timezone"] == "Pacific/Auckland"
    assert r.json()["local_date"] == "2030-03-10"
    assert len(r.json()["legs"]) == 5


def test_reprocess_refuses_annotated_track(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    track_id = _upload(admin_client, trip.id, _synthetic_day())["track_id"]
    track = db_session.get(GpsTrack, track_id)
    assert track is not None
    track.legs_source = "annotated"
    db_session.commit()
    r = admin_client.post(f"/api/v1/travels/gps-tracks/{track_id}/reprocess", json={})
    assert r.status_code == 409


def test_raw_download_and_delete(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    content = _synthetic_day()
    track_id = _upload(admin_client, trip.id, content)["track_id"]

    r = admin_client.get(f"/api/v1/travels/gps-tracks/{track_id}/raw")
    assert r.content == content
    assert "10080000.CSV" in r.headers["content-disposition"]

    assert admin_client.delete(f"/api/v1/travels/gps-tracks/{track_id}").status_code == 204
    assert storage.files == {}
    assert db_session.query(GpsTrackLeg).count() == 0


def test_tracks_are_admin_only(client: TestClient, db_session: Session) -> None:
    trip = _trip(db_session)
    assert client.get(f"/api/v1/travels/trips/{trip.id}/gps-tracks").status_code in (401, 403)


# ---------------------------------------------------------------------------
# Analysis upload
# ---------------------------------------------------------------------------


def _iso(minutes: float, start: datetime = START) -> str:
    """Time `minutes` after START, written in a non-UTC offset on purpose."""
    t = (start + timedelta(minutes=minutes)).astimezone(timezone(timedelta(hours=-3)))
    return t.isoformat()


def _analysis(legs: list[dict], **day: str) -> dict:
    return {
        "format": "rembish-gps-analysis/1",
        "days": [{"source_file": "10080000.CSV", "title": "Test day", **day, "legs": legs}],
    }


SYNTHETIC_LEGS = [
    {"start": _iso(0), "end": _iso(10), "mode": "walk", "title": "Old town"},
    {"start": _iso(10), "end": _iso(30), "mode": "stop", "title": "Café", "hidden": True},
    {"start": _iso(30), "end": _iso(45), "mode": "bus", "title": "Bus to the coast"},
    {"start": _iso(45), "end": _iso(54), "mode": "gap", "note": "Tunnel"},
    {"start": _iso(54), "end": _iso(64), "mode": "walk", "title": "Harbour"},
]


def test_leg_modes_match_model() -> None:
    from src.models.gps import LEG_MODES as MODEL_MODES
    from src.travels.gps_processing import LEG_MODES

    assert LEG_MODES == MODEL_MODES


def test_parse_time_requires_offset() -> None:
    from src.travels.gps_processing import parse_time

    assert parse_time("2030-03-10T05:00:00-03:00") == START
    with pytest.raises(ValueError, match="offset"):
        parse_time("2030-03-10T05:00:00")


def test_analysis_replaces_legs_and_recomputes(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    track_id = _upload(admin_client, trip.id, _synthetic_day())["track_id"]

    r = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/gps-tracks/analysis", json=_analysis(SYNTHETIC_LEGS)
    )
    assert r.status_code == 200, r.text
    assert r.json()["days"] == [{"source_file": "10080000.CSV", "track_id": track_id, "legs": 5}]

    day = admin_client.get(f"/api/v1/travels/trips/{trip.id}/gps-tracks").json()["tracks"][0]
    assert day["legs_source"] == "annotated"
    assert day["title"] == "Test day"
    walk, cafe, bus, gap, _ = day["legs"]
    assert [leg["mode"] for leg in day["legs"]] == ["walk", "stop", "bus", "gap", "walk"]
    assert walk["distance_km"] == pytest.approx(0.83, abs=0.05)
    assert bus["distance_km"] == pytest.approx(15.0, abs=0.5)
    assert bus["title"] == "Bus to the coast"
    assert cafe["is_hidden"] is True and cafe["lines"] == []
    assert gap["note"] == "Tunnel" and gap["distance_km"] == pytest.approx(3.0, abs=0.1)
    assert walk["started_at"] == "2030-03-10T08:00:00Z"


def test_analysis_is_all_or_nothing(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    _upload(admin_client, trip.id, _synthetic_day())
    bad = [
        {"start": _iso(0), "end": _iso(20), "mode": "walk"},
        {"start": _iso(10), "end": _iso(30), "mode": "hovercraft"},
        {"start": "2030-03-10T09:00:00", "end": _iso(64), "mode": "car"},
    ]
    r = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/gps-tracks/analysis",
        json={
            "format": "rembish-gps-analysis/1",
            "days": [
                {"source_file": "10080000.CSV", "legs": bad[:2]},
                {"source_file": "missing.CSV", "legs": bad[:1]},
            ],
        },
    )
    assert r.status_code == 422
    detail = " | ".join(r.json()["detail"])
    assert "unknown mode 'hovercraft'" in detail
    assert "overlaps" in detail
    assert "missing.CSV: no matching track" in detail
    track = db_session.query(GpsTrack).one()
    assert track.legs_source == "auto"


def test_analysis_rejects_naive_times_and_wrong_format(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    _upload(admin_client, trip.id, _synthetic_day())
    url = f"/api/v1/travels/trips/{trip.id}/gps-tracks/analysis"
    naive = [{"start": "2030-03-10T08:00:00", "end": _iso(10), "mode": "walk"}]
    r = admin_client.post(url, json=_analysis(naive))
    assert r.status_code == 422 and "without offset" in r.json()["detail"][0]
    r = admin_client.post(url, json={**_analysis(SYNTHETIC_LEGS), "format": "something/2"})
    assert r.status_code == 422


def test_analysis_window_outside_track_is_rejected(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    _upload(admin_client, trip.id, _synthetic_day())
    late = [{"start": _iso(60), "end": _iso(120), "mode": "walk"}]
    r = admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/gps-tracks/analysis", json=_analysis(late)
    )
    assert r.status_code == 422 and "outside the track" in r.json()["detail"][0]


def test_discard_analysis_restores_auto_legs(
    admin_client: TestClient, db_session: Session, storage: FakeStorage
) -> None:
    trip = _trip(db_session)
    track_id = _upload(admin_client, trip.id, _synthetic_day())["track_id"]
    admin_client.post(
        f"/api/v1/travels/trips/{trip.id}/gps-tracks/analysis", json=_analysis(SYNTHETIC_LEGS)
    )
    r = admin_client.post(
        f"/api/v1/travels/gps-tracks/{track_id}/reprocess", json={"discard_analysis": True}
    )
    assert r.status_code == 200
    assert r.json()["legs_source"] == "auto"
    assert r.json()["title"] is None
    assert [leg["mode"] for leg in r.json()["legs"]] == ["foot", "stop", "vehicle", "gap", "foot"]
