"""Tests for NomadMania regions upload endpoint."""

from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy.orm import Session

from src.models import NMRegion


def _make_xlsx(rows: list[list]) -> bytes:
    """Create a minimal XLSX file with given rows (no header)."""
    wb = Workbook()
    ws = wb.active
    # Header row (row 1, skipped by parser)
    ws.append(["Region", "Visited", "First Year", "Last Year"])
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_upload_nm_regions(admin_client: TestClient, db_session: Session) -> None:
    """Successful upload parses and stores regions."""
    xlsx = _make_xlsx([
        ["Czechia – Prague", 1, 2015, 2025],
        ["Czechia – Brno", 0, None, None],
        ["Germany – Berlin", 1, 2018, 2023],
    ])

    res = admin_client.post(
        "/api/v1/travels/upload-nm",
        files={"file": ("regions.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert data["visited"] == 2
    assert "3 regions" in data["message"]

    # Verify DB
    regions = db_session.query(NMRegion).all()
    assert len(regions) == 3

    prague = next(r for r in regions if "Prague" in r.name)
    assert prague.country == "Czechia"
    assert prague.visited is True
    assert prague.first_visited_year == 2015


def test_upload_nm_rejects_non_xlsx(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/travels/upload-nm",
        files={"file": ("data.csv", b"a,b,c", "text/csv")},
    )
    assert res.status_code == 400
    assert "xlsx" in res.json()["detail"].lower()


def test_upload_nm_rejects_empty(admin_client: TestClient) -> None:
    """XLSX with no data rows is rejected."""
    xlsx = _make_xlsx([])  # header only

    res = admin_client.post(
        "/api/v1/travels/upload-nm",
        files={"file": ("empty.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 400
    assert "no valid" in res.json()["detail"].lower()


def test_upload_nm_replaces_existing(admin_client: TestClient, db_session: Session) -> None:
    """Second upload replaces all regions."""
    xlsx1 = _make_xlsx([["Region A", 1, 2020, 2020]])
    admin_client.post(
        "/api/v1/travels/upload-nm",
        files={"file": ("r.xlsx", xlsx1, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert db_session.query(NMRegion).count() == 1

    xlsx2 = _make_xlsx([["Region B", 0, None, None], ["Region C", 1, 2021, 2021]])
    admin_client.post(
        "/api/v1/travels/upload-nm",
        files={"file": ("r.xlsx", xlsx2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert db_session.query(NMRegion).count() == 2


def test_upload_extract_country() -> None:
    """Unit test for country extraction from region names."""
    from src.travels.upload import extract_country

    assert extract_country("Czechia – Prague") == "Czechia"
    assert extract_country("Germany - Berlin") == "Germany"
    assert extract_country("Timor-Leste – Dili") == "Timor-Leste"
    assert extract_country("Monaco") == "Monaco"


def test_upload_requires_admin(client: TestClient) -> None:
    xlsx = _make_xlsx([["Test", 0, None, None]])
    res = client.post(
        "/api/v1/travels/upload-nm",
        files={"file": ("r.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 401
