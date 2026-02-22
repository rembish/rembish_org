"""Tests for the travel map OG preview image endpoint."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import TCCDestination, Trip, TripDestination, UNCountry, Visit
from src.travels.map_image import (
    _decode_arcs,
    _hsl_to_rgb,
    _load_topo,
    _normalize_ring,
    _resolve_geometry,
    _resolve_ring,
    _visit_color,
    _visit_hue,
    _visit_lightness,
)


# ---------------------------------------------------------------------------
# TopoJSON decoder
# ---------------------------------------------------------------------------


def test_load_topo() -> None:
    """TopoJSON loads and has expected structure."""
    topo = _load_topo()
    assert topo["type"] == "Topology"
    assert "arcs" in topo
    assert "countries" in topo["objects"]


def test_decode_arcs() -> None:
    """Delta-encoded arcs decode to lon/lat coordinate lists."""
    topo = _load_topo()
    arcs = _decode_arcs(topo)
    assert len(arcs) > 0
    # Each arc should be a list of (lon, lat) tuples
    for coord in arcs[0]:
        lon, lat = coord
        assert -180.0 <= lon <= 180.0
        assert -90.0 <= lat <= 90.0


def test_resolve_ring() -> None:
    """Ring resolution concatenates arcs, handling reversed refs."""
    arcs = [
        [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)],
        [(3.0, 3.0), (4.0, 4.0)],
    ]
    # Forward reference
    ring = _resolve_ring([0, 1], arcs)
    assert ring[0] == (0.0, 0.0)
    assert ring[-1] == (4.0, 4.0)
    # Negative reference = reversed arc (index ~(-1) = 0)
    ring2 = _resolve_ring([-1], arcs)
    assert ring2[0] == (2.0, 2.0)
    assert ring2[-1] == (0.0, 0.0)


def test_resolve_geometry_polygon() -> None:
    """Polygon geometry resolves to list of rings."""
    arcs = [[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0)]]
    geom = {"type": "Polygon", "arcs": [[0]]}
    rings = _resolve_geometry(geom, arcs)
    assert len(rings) == 1
    assert len(rings[0]) == 4


def test_resolve_geometry_multipolygon() -> None:
    """MultiPolygon geometry resolves to multiple rings."""
    arcs = [
        [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0)],
        [(5.0, 5.0), (6.0, 5.0), (6.0, 6.0), (5.0, 5.0)],
    ]
    geom = {"type": "MultiPolygon", "arcs": [[[0]], [[1]]]}
    rings = _resolve_geometry(geom, arcs)
    assert len(rings) == 2


# ---------------------------------------------------------------------------
# Antimeridian normalization
# ---------------------------------------------------------------------------


def test_normalize_ring_no_crossing() -> None:
    """Non-crossing ring is returned unchanged."""
    ring = [(10.0, 50.0), (20.0, 50.0), (20.0, 60.0), (10.0, 50.0)]
    assert _normalize_ring(ring) is ring  # same object, no copy


def test_normalize_ring_crossing() -> None:
    """Antimeridian-crossing ring shifts negative lons to positive."""
    ring = [(170.0, 60.0), (175.0, 65.0), (-170.0, 65.0), (-175.0, 60.0)]
    normalized = _normalize_ring(ring)
    # -170 should become 190, -175 should become 185
    assert normalized[2] == (190.0, 65.0)
    assert normalized[3] == (185.0, 60.0)
    # Positive lons unchanged
    assert normalized[0] == (170.0, 60.0)
    assert normalized[1] == (175.0, 65.0)


# ---------------------------------------------------------------------------
# Color calculation
# ---------------------------------------------------------------------------


def test_visit_hue_single() -> None:
    """Single visit gives blue hue (210)."""
    assert _visit_hue(1) == 210.0


def test_visit_hue_many() -> None:
    """Many visits converge toward warm hues."""
    assert _visit_hue(5) < _visit_hue(1)
    assert _visit_hue(15) < _visit_hue(5)
    assert _visit_hue(50) >= 15.0


def test_visit_lightness_old() -> None:
    """Pre-2010 visits get darkest lightness."""
    assert _visit_lightness(date(2005, 1, 1), date(2025, 1, 1)) == 0.35


def test_visit_lightness_recent() -> None:
    """Newest visit gets lightest value."""
    newest = date(2025, 6, 1)
    assert _visit_lightness(newest, newest) == 0.60


def test_hsl_to_rgb_blue() -> None:
    """HSL blue (210, 70%, 50%) converts to an RGB with dominant blue."""
    r, g, b = _hsl_to_rgb(210.0, 0.70, 0.50)
    assert b > r
    assert b > g


def test_visit_color_returns_rgb() -> None:
    """visit_color returns a valid RGB tuple."""
    color = _visit_color(date(2023, 5, 1), date(2025, 1, 1), 3)
    assert len(color) == 3
    assert all(0 <= c <= 255 for c in color)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


def test_og_map_endpoint(client: TestClient) -> None:
    """GET /api/v1/travels/og/map.png returns a PNG image."""
    r = client.get("/api/v1/travels/og/map.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    # PNG magic bytes
    assert r.content[:4] == b"\x89PNG"


def test_og_map_with_visits(client: TestClient, db_session: Session) -> None:
    """Map renders with visited countries colored."""
    country = UNCountry(
        name="Testland",
        iso_alpha2="TL",
        iso_alpha3="TLD",
        iso_numeric="999",
        continent="Europe",
        map_region_codes="999",
        capital_lat=50.0,
        capital_lng=10.0,
    )
    db_session.add(country)
    db_session.flush()
    tcc = TCCDestination(
        name="Testland Main",
        tcc_region="EUROPE & MEDITERRANEAN",
        tcc_index=100,
        un_country_id=country.id,
    )
    db_session.add(tcc)
    db_session.flush()
    visit = Visit(tcc_destination_id=tcc.id, first_visit_date=date(2023, 5, 1))
    db_session.add(visit)
    db_session.commit()

    r = client.get("/api/v1/travels/og/map.png")
    assert r.status_code == 200
    assert r.content[:4] == b"\x89PNG"


# ---------------------------------------------------------------------------
# OG tags for /travels include map image
# ---------------------------------------------------------------------------


def test_og_travels_uses_map_image(client: TestClient) -> None:
    """/travels OG tags point to the map.png image."""
    r = client.get("/api/v1/og", params={"path": "/travels"})
    assert r.status_code == 200
    assert "/api/v1/travels/og/map.png" in r.text
    assert 'og:image:width" content="1200"' in r.text
    assert 'og:image:height" content="630"' in r.text


def test_og_travels_dynamic_stats(client: TestClient, db_session: Session) -> None:
    """/travels OG description includes dynamic visit stats."""
    country = UNCountry(
        name="Testland",
        iso_alpha2="TL",
        iso_alpha3="TLD",
        iso_numeric="999",
        continent="Europe",
        map_region_codes="999",
        capital_lat=50.0,
        capital_lng=10.0,
    )
    db_session.add(country)
    db_session.flush()
    tcc = TCCDestination(
        name="Testland Main",
        tcc_region="EUROPE & MEDITERRANEAN",
        tcc_index=100,
        un_country_id=country.id,
    )
    db_session.add(tcc)
    db_session.flush()
    visit = Visit(tcc_destination_id=tcc.id, first_visit_date=date(2023, 5, 1))
    db_session.add(visit)
    db_session.commit()

    r = client.get("/api/v1/og", params={"path": "/travels"})
    assert r.status_code == 200
    # Should show "1 of N UN countries" in the description
    assert "1 of" in r.text
    assert "UN countries" in r.text
    assert "TCC destinations" in r.text
