"""Generate a static PNG world map showing visited countries for OG preview."""

import colorsys
import io
import json
from datetime import date
from pathlib import Path

from cachetools import TTLCache
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from PIL import Image, ImageDraw
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TCCDestination, Trip, TripDestination, UNCountry, Visit

router = APIRouter()

# --- TopoJSON loading and decoding ---

_TOPO_PATH = Path(__file__).resolve().parent.parent / "data" / "world-110m.json"
_topo: dict | None = None


def _load_topo() -> dict:
    global _topo
    if _topo is None:
        with open(_TOPO_PATH) as f:
            _topo = json.load(f)
    return _topo


def _decode_arcs(topo: dict) -> list[list[tuple[float, float]]]:
    """Decode delta-encoded TopoJSON arcs into (lon, lat) coordinate lists."""
    raw_arcs = topo["arcs"]
    scale = topo["transform"]["scale"]
    translate = topo["transform"]["translate"]
    decoded: list[list[tuple[float, float]]] = []

    for arc in raw_arcs:
        coords: list[tuple[float, float]] = []
        x = 0
        y = 0
        for dx, dy in arc:
            x += dx
            y += dy
            lon = x * scale[0] + translate[0]
            lat = y * scale[1] + translate[1]
            coords.append((lon, lat))
        decoded.append(coords)
    return decoded


def _resolve_geometry(
    geom: dict, arcs: list[list[tuple[float, float]]]
) -> list[list[tuple[float, float]]]:
    """Resolve a TopoJSON geometry into a list of polygon rings (lon, lat)."""
    polygons: list[list[tuple[float, float]]] = []
    geom_type = geom["type"]

    if geom_type == "Polygon":
        for ring_refs in geom["arcs"]:
            polygons.append(_resolve_ring(ring_refs, arcs))
    elif geom_type == "MultiPolygon":
        for polygon_refs in geom["arcs"]:
            for ring_refs in polygon_refs:
                polygons.append(_resolve_ring(ring_refs, arcs))
    return polygons


def _resolve_ring(
    arc_refs: list[int], arcs: list[list[tuple[float, float]]]
) -> list[tuple[float, float]]:
    """Resolve arc references into a single coordinate ring."""
    coords: list[tuple[float, float]] = []
    for ref in arc_refs:
        if ref >= 0:
            arc_coords = arcs[ref]
        else:
            arc_coords = list(reversed(arcs[~ref]))
        # Avoid duplicate join points
        if coords and arc_coords:
            coords.extend(arc_coords[1:])
        else:
            coords.extend(arc_coords)
    return coords


# --- Color calculation (port of frontend getVisitColor) ---

_BASELINE_DATE = date(2010, 1, 1)


def _visit_hue(visit_count: int) -> float:
    if visit_count <= 1:
        return 210.0
    elif visit_count <= 5:
        return 210.0 - (visit_count - 1) * 15.0
    elif visit_count <= 15:
        return 150.0 - (visit_count - 5) * 7.0
    elif visit_count <= 30:
        return 80.0 - (visit_count - 15) * 2.5
    else:
        return max(15.0, 42.0 - (visit_count - 30) * 0.5)


def _visit_lightness(visit_date: date, newest_date: date) -> float:
    if visit_date < _BASELINE_DATE:
        return 0.35
    total_range = (newest_date - _BASELINE_DATE).days
    if total_range == 0:
        return 0.50
    ratio = (visit_date - _BASELINE_DATE).days / total_range
    return 0.35 + ratio * 0.25


def _hsl_to_rgb(h: float, s: float, lightness: float) -> tuple[int, int, int]:
    """Convert HSL (h in degrees, s/lightness in 0-1) to RGB (0-255)."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, lightness, s)
    return int(r * 255), int(g * 255), int(b * 255)


def _visit_color(visit_date: date, newest_date: date, visit_count: int) -> tuple[int, int, int]:
    hue = _visit_hue(visit_count)
    lightness = _visit_lightness(visit_date, newest_date)
    return _hsl_to_rgb(hue, 0.70, lightness)


_UNVISITED_COLOR = (230, 233, 236)
_BG_COLOR = (240, 242, 244)
_OUTLINE_COLOR = (200, 200, 200)

# --- Projection ---

_IMG_W = 1200
_IMG_H = 630
_PAD = 8

# Visible lat/lon window — cropped to exclude Antarctica and reduce dead space.
# Shifted 10° west so Alaska isn't right at the edge.
_LON_MIN = -170.0
_LON_MAX = 190.0  # 10° past antimeridian to keep Russia's east coast
_LAT_MIN = -58.0  # just south of Tierra del Fuego
_LAT_MAX = 85.0

_LON_RANGE = _LON_MAX - _LON_MIN  # 360°
_LAT_RANGE = _LAT_MAX - _LAT_MIN  # 143°

_MAP_W = _IMG_W - 2 * _PAD
_MAP_H = _IMG_H - 2 * _PAD


def _project(lon: float, lat: float) -> tuple[float, float]:
    """Equirectangular projection to pixel coords with custom viewport."""
    x = (lon - _LON_MIN) / _LON_RANGE * _MAP_W + _PAD
    y = (_LAT_MAX - lat) / _LAT_RANGE * _MAP_H + _PAD
    return x, y


# --- Map data query (reuses logic from data.py's get_map_data) ---


def _query_map_colors(
    db: Session,
) -> dict[str, tuple[date, int]]:
    """Return {region_code: (first_visit_date, trip_count)} for visited regions."""
    today = date.today()
    regions: dict[str, tuple[date, int]] = {}

    # Trip counts per UN country
    un_trip_counts_q = (
        db.query(
            TCCDestination.un_country_id,
            func.count(func.distinct(TripDestination.trip_id)),
        )
        .join(TripDestination, TripDestination.tcc_destination_id == TCCDestination.id)
        .join(Trip, Trip.id == TripDestination.trip_id)
        .filter(TCCDestination.un_country_id.isnot(None))
        .filter(Trip.start_date <= today)
        .group_by(TCCDestination.un_country_id)
        .all()
    )
    un_trip_counts = {un_id: count for un_id, count in un_trip_counts_q}

    # Trip counts per TCC destination
    tcc_trip_counts_q = (
        db.query(
            TripDestination.tcc_destination_id,
            func.count(func.distinct(TripDestination.trip_id)),
        )
        .join(Trip, Trip.id == TripDestination.trip_id)
        .filter(Trip.start_date <= today)
        .group_by(TripDestination.tcc_destination_id)
        .all()
    )
    tcc_trip_counts = {tcc_id: count for tcc_id, count in tcc_trip_counts_q}

    # Visited UN countries
    visited_un = (
        db.query(UNCountry, func.min(Visit.first_visit_date).label("first_visit"))
        .join(TCCDestination, TCCDestination.un_country_id == UNCountry.id)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(Visit.first_visit_date <= today)
        .group_by(UNCountry.id)
        .all()
    )
    for country, first_visit in visited_un:
        trip_count = un_trip_counts.get(country.id, 0)
        for code in country.map_region_codes.split(","):
            code = code.strip()
            if code and first_visit:
                if code not in regions or first_visit < regions[code][0]:
                    regions[code] = (first_visit, trip_count)

    # Non-UN territories with own polygons (Kosovo, Somaliland, etc.)
    visited_tcc = (
        db.query(TCCDestination, Visit.first_visit_date)
        .join(Visit, Visit.tcc_destination_id == TCCDestination.id)
        .filter(
            TCCDestination.map_region_code.isnot(None),
            TCCDestination.un_country_id.is_(None),
            Visit.first_visit_date <= today,
        )
        .all()
    )
    for dest, first_visit in visited_tcc:
        if dest.map_region_code and first_visit:
            code = dest.map_region_code
            if code not in regions or first_visit < regions[code][0]:
                regions[code] = (first_visit, tcc_trip_counts.get(dest.id, 0))

    return regions


def _normalize_ring(
    ring: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """Shift longitudes in antimeridian-crossing rings to avoid coordinate jumps.

    For rings that cross ±180° (e.g. Russia), shifts negative longitudes to
    positive (lon + 360) so the polygon draws continuously. Points that end up
    beyond the map edge are simply off-screen rather than causing artifacts.
    """
    crosses = False
    for i in range(len(ring) - 1):
        if abs(ring[i + 1][0] - ring[i][0]) > 180.0:
            crosses = True
            break
    if not crosses:
        return ring
    return [(lon + 360.0 if lon < 0 else lon, lat) for lon, lat in ring]


# --- Rendering ---

_cache: TTLCache[str, bytes] = TTLCache(maxsize=1, ttl=3600)


def _render_map(db: Session) -> bytes:
    topo = _load_topo()
    arcs = _decode_arcs(topo)
    geometries = topo["objects"]["countries"]["geometries"]

    region_colors = _query_map_colors(db)

    # Find newest date for lightness calculation
    newest = date.today()
    if region_colors:
        newest = max(d for d, _ in region_colors.values())

    img = Image.new("RGB", (_IMG_W, _IMG_H), _BG_COLOR)
    draw = ImageDraw.Draw(img)

    for geom in geometries:
        geo_id = str(geom.get("id", ""))
        # Skip Antarctica (010) — wraps 360° and causes fill artifacts
        if geo_id == "010":
            continue
        polygons = _resolve_geometry(geom, arcs)

        if geo_id in region_colors:
            visit_date, trip_count = region_colors[geo_id]
            fill = _visit_color(visit_date, newest, trip_count)
        else:
            fill = _UNVISITED_COLOR

        for ring in polygons:
            ring = _normalize_ring(ring)
            projected = [_project(lon, lat) for lon, lat in ring]
            if len(projected) >= 3:
                draw.polygon(projected, fill=fill, outline=_OUTLINE_COLOR)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@router.get("/og/map.png")
def get_og_map_image(db: Session = Depends(get_db)) -> Response:
    """Serve a static PNG world map with visited countries colored."""
    cached = _cache.get("map")
    if cached:
        return Response(content=cached, media_type="image/png")

    png_bytes = _render_map(db)
    _cache["map"] = png_bytes
    return Response(content=png_bytes, media_type="image/png")
