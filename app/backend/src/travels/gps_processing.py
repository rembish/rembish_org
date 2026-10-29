"""GNSS logger CSV parsing (Columbus-style format) and automatic leg detection.

Pure functions, no database or network. The method follows the ops research notes:
median speed decides foot vs vehicle, short blips are absorbed, gaps of 5+ minutes
are stops (or "gap" legs when the logger moved without a fix), and each leg's
polyline is simplified with Ramer-Douglas-Peucker. Boats and place names are not
detected here — they come from the manual analysis upload, whose time windows are
turned into legs by legs_from_windows() (shared with the ops analysis tool, which
loads this file by path — keep it standard-library only).
"""

import bisect
import csv
import io
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

# Bumped whenever the output of process_points() changes, so old tracks can be found
# and reprocessed.
PROCESSING_VERSION = 1

SEGMENT_GAP_S = 60  # split polylines when points are further apart than this
STOP_GAP_S = 300  # a gap this long between points is a stop
VEHICLE_KMH = 12.0  # median speed above this is a vehicle
MEDIAN_HALF_WINDOW = 15  # points either side (1 Hz logging, so about ±15 s)
SHORT_FOOT_IN_VEHICLE_S = 240  # traffic: a short "walk" between two drives
SHORT_BLIP_S = 60  # any shorter run between two runs of the same mode
STATIONARY_RADIUS_M = 100  # a long walk that stays within this radius is a stop
STATIONARY_MIN_S = 600
DROPOUT_M = 500  # a gap that moved further than this is missing data, not a stop
GLITCH_KMH = 400  # points implying a faster jump are dropped as glitches
EPS_VEHICLE = 6e-5  # RDP tolerance in degrees (about 6 m)
EPS_FOOT = 1.2e-5  # about 1.2 m — keeps walks recognisable

ANALYSIS_FORMAT = "rembish-gps-analysis/1"
# Mirrors models.gps.LEG_MODES (kept separate so this file stays importable alone).
LEG_MODES = (
    "stop",
    "gap",
    "foot",
    "vehicle",
    "walk",
    "bicycle",
    "animal",
    "car",
    "bus",
    "motorbike",
    "train",
    "tram",
    "metro",
    "boat",
    "ferry",
    "plane",
    "cable_car",
)
# Slow modes keep the fine simplification tolerance; everything else is simplified harder.
FINE_MODES = {"foot", "walk", "bicycle", "animal", "boat"}
WINDOW_SLACK = timedelta(minutes=2)  # windows may start/end this far outside the track
MAX_TITLE = 200

REQUIRED_COLUMNS = {"TAG", "DATE", "TIME", "LATITUDE N/S", "LONGITUDE E/W", "SPEED"}


@dataclass(frozen=True)
class Point:
    tag: str
    t: datetime  # UTC, timezone-aware
    lat: float
    lon: float
    speed_kmh: float


@dataclass
class Leg:
    mode: str  # stop | foot | vehicle | boat | gap
    started_at: datetime
    ended_at: datetime
    lat: float
    lon: float
    distance_km: float = 0.0
    max_speed_kmh: float = 0.0
    lines: list[list[list[float]]] = field(default_factory=list)
    title: str | None = None
    note: str | None = None
    is_hidden: bool = False


@dataclass
class ProcessedTrack:
    started_at: datetime
    ended_at: datetime
    point_count: int
    wake_count: int
    poi_count: int
    distance_km: float
    max_speed_kmh: float
    legs: list[Leg]


@dataclass
class _Run:
    mode: str
    pts: list[Point]

    @property
    def start(self) -> datetime:
        return self.pts[0].t

    @property
    def end(self) -> datetime:
        return self.pts[-1].t

    @property
    def duration_s(self) -> float:
        return (self.end - self.start).total_seconds()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _coord(value: str) -> float:
    value = value.strip()
    hemisphere = value[-1].upper()
    number = float(value[:-1])
    if hemisphere in ("S", "W"):
        return -number
    if hemisphere in ("N", "E"):
        return number
    raise ValueError(f"Bad coordinate: {value}")


def parse_csv(content: bytes) -> list[Point]:
    """Parse a logger CSV into points sorted by time. Malformed rows are skipped."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    columns = {c.strip() for c in (reader.fieldnames or [])}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"Not a logger CSV, missing columns: {', '.join(sorted(missing))}")

    points: list[Point] = []
    for row in reader:
        row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        try:
            t = datetime.strptime(row["DATE"] + row["TIME"], "%y%m%d%H%M%S").replace(tzinfo=UTC)
            lat = _coord(row["LATITUDE N/S"])
            lon = _coord(row["LONGITUDE E/W"])
            speed = float(row["SPEED"] or 0)
        except (ValueError, IndexError, KeyError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        points.append(Point(tag=row["TAG"], t=t, lat=lat, lon=lon, speed_kmh=speed))

    points.sort(key=lambda p: p.t)
    return _drop_glitches(points)


def _drop_glitches(points: list[Point]) -> list[Point]:
    """Drop duplicate timestamps and points implying an impossible jump."""
    out: list[Point] = []
    for p in points:
        if out:
            prev = out[-1]
            dt = (p.t - prev.t).total_seconds()
            if dt <= 0:
                continue
            if distance_m(prev, p) / dt * 3.6 > GLITCH_KMH:
                continue
        out.append(p)
    return out


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def distance_m(a: Point, b: Point) -> float:
    """Haversine distance in metres."""
    r = 6371000.0
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp = p2 - p1
    dl = math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _path_km(pts: list[Point]) -> float:
    total = 0.0
    for a, b in zip(pts, pts[1:], strict=False):
        if (b.t - a.t).total_seconds() <= SEGMENT_GAP_S:
            total += distance_m(a, b)
    return total / 1000


def simplify(coords: list[list[float]], epsilon: float) -> list[list[float]]:
    """Iterative Ramer-Douglas-Peucker (recursion would overflow on long drives)."""
    n = len(coords)
    if n <= 2:
        return coords
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        lo, hi = stack.pop()
        (y1, x1), (y2, x2) = coords[lo], coords[hi]
        dy, dx = y2 - y1, x2 - x1
        norm = math.hypot(dx, dy)
        best, best_i = 0.0, -1
        for i in range(lo + 1, hi):
            y, x = coords[i]
            if norm == 0:
                d = math.hypot(x - x1, y - y1)
            else:
                d = abs(dy * (x - x1) - dx * (y - y1)) / norm
            if d > best:
                best, best_i = d, i
        if best > epsilon and best_i > 0:
            keep[best_i] = True
            stack.append((lo, best_i))
            stack.append((best_i, hi))
    return [c for c, k in zip(coords, keep, strict=True) if k]


def _lines(pts: list[Point], epsilon: float) -> list[list[list[float]]]:
    """Split points into polylines at pauses, simplify each, round to ~10 cm."""
    lines: list[list[list[float]]] = []
    current: list[Point] = []
    for p in pts:
        if current and (p.t - current[-1].t).total_seconds() > SEGMENT_GAP_S:
            lines.append(_encode(current, epsilon))
            current = []
        current.append(p)
    if current:
        lines.append(_encode(current, epsilon))
    return lines


def _encode(pts: list[Point], epsilon: float) -> list[list[float]]:
    coords = simplify([[p.lat, p.lon] for p in pts], epsilon)
    return [[round(lat, 6), round(lon, 6)] for lat, lon in coords]


def _centroid(pts: list[Point]) -> tuple[float, float]:
    return sum(p.lat for p in pts) / len(pts), sum(p.lon for p in pts) / len(pts)


# ---------------------------------------------------------------------------
# Leg detection
# ---------------------------------------------------------------------------


def _point_modes(points: list[Point]) -> list[str]:
    speeds = [p.speed_kmh for p in points]
    modes: list[str] = []
    for i in range(len(points)):
        window = sorted(speeds[max(0, i - MEDIAN_HALF_WINDOW) : i + MEDIAN_HALF_WINDOW + 1])
        modes.append("vehicle" if window[len(window) // 2] > VEHICLE_KMH else "foot")
    return modes


def _runs(points: list[Point], modes: list[str]) -> list[_Run]:
    runs: list[_Run] = []
    for i, p in enumerate(points):
        gap = i > 0 and (p.t - points[i - 1].t).total_seconds() >= STOP_GAP_S
        if not runs or runs[-1].mode != modes[i] or gap:
            runs.append(_Run(mode=modes[i], pts=[]))
        runs[-1].pts.append(p)
    return _merge_runs(runs)


def _gap_s(a: _Run, b: _Run) -> float:
    return (b.start - a.end).total_seconds()


def _merge_runs(runs: list[_Run]) -> list[_Run]:
    changed = True
    while changed:
        changed = False
        for i, run in enumerate(runs):
            prev = runs[i - 1] if i > 0 else None
            nxt = runs[i + 1] if i + 1 < len(runs) else None
            if prev and prev.mode == run.mode and _gap_s(prev, run) < STOP_GAP_S:
                prev.pts += run.pts
                del runs[i]
                changed = True
                break
            limit = SHORT_FOOT_IN_VEHICLE_S if run.mode == "foot" else SHORT_BLIP_S
            if (
                prev
                and nxt
                and prev.mode == nxt.mode != run.mode
                and run.duration_s < limit
                and _gap_s(prev, run) < STOP_GAP_S
                and _gap_s(run, nxt) < STOP_GAP_S
            ):
                prev.pts += run.pts + nxt.pts
                del runs[i : i + 2]
                changed = True
                break
    return runs


def _stays_put(run: _Run) -> bool:
    """A walk that never leaves a small circle: shuffling around, not going anywhere."""
    if run.mode != "foot":
        return False
    lat, lon = _centroid(run.pts)
    centre = Point(tag="T", t=run.start, lat=lat, lon=lon, speed_kmh=0)
    return all(distance_m(centre, p) <= STATIONARY_RADIUS_M for p in run.pts)


def _stop_leg(run: _Run) -> Leg:
    lat, lon = _centroid(run.pts)
    return Leg(mode="stop", started_at=run.start, ended_at=run.end, lat=lat, lon=lon)


def _run_leg(run: _Run) -> Leg:
    lat, lon = _centroid(run.pts)
    eps = EPS_VEHICLE if run.mode == "vehicle" else EPS_FOOT
    return Leg(
        mode=run.mode,
        started_at=run.start,
        ended_at=run.end,
        lat=lat,
        lon=lon,
        distance_km=round(_path_km(run.pts), 3),
        max_speed_kmh=max(p.speed_kmh for p in run.pts),
        lines=_lines(run.pts, eps),
    )


def _between_leg(prev: _Run, nxt: _Run) -> Leg:
    a, b = prev.pts[-1], nxt.pts[0]
    moved = distance_m(a, b)
    if moved > DROPOUT_M:
        return Leg(
            mode="gap",
            started_at=a.t,
            ended_at=b.t,
            lat=(a.lat + b.lat) / 2,
            lon=(a.lon + b.lon) / 2,
            distance_km=round(moved / 1000, 3),
            lines=[[[round(a.lat, 6), round(a.lon, 6)], [round(b.lat, 6), round(b.lon, 6)]]],
        )
    return Leg(mode="stop", started_at=a.t, ended_at=b.t, lat=a.lat, lon=a.lon)


def _merge_stops(legs: list[Leg]) -> list[Leg]:
    out: list[Leg] = []
    for leg in legs:
        if out and leg.mode == "stop" and out[-1].mode == "stop":
            out[-1].ended_at = leg.ended_at
            continue
        out.append(leg)
    return out


def process_points(points: list[Point]) -> ProcessedTrack:
    """Turn parsed points into legs and day totals."""
    if not points:
        raise ValueError("Track has no valid points")

    runs = _runs(points, _point_modes(points))
    # (leg, run that stayed put) — the flag decides below whether a short walk is a stop
    pending: list[tuple[Leg, bool]] = []
    for i, run in enumerate(runs):
        if i > 0 and _gap_s(runs[i - 1], run) >= STOP_GAP_S:
            pending.append((_between_leg(runs[i - 1], run), False))
        if _stays_put(run) and run.duration_s >= STATIONARY_MIN_S:
            pending.append((_stop_leg(run), False))
        else:
            pending.append((_run_leg(run), _stays_put(run)))

    # A walk that stayed put next to a stop (or at either end of the day) is part of
    # that stop: the logger waking up, a few steps around the table.
    legs: list[Leg] = []
    for i, (leg, stayed) in enumerate(pending):
        if stayed:
            before = pending[i - 1][0].mode if i > 0 else "stop"
            after = pending[i + 1][0].mode if i + 1 < len(pending) else "stop"
            if "stop" in (before, after):
                leg = Leg(
                    mode="stop",
                    started_at=leg.started_at,
                    ended_at=leg.ended_at,
                    lat=leg.lat,
                    lon=leg.lon,
                )
        legs.append(leg)
    legs = _merge_stops(legs)

    return ProcessedTrack(
        started_at=points[0].t,
        ended_at=points[-1].t,
        point_count=len(points),
        wake_count=sum(1 for p in points if p.tag == "G"),
        poi_count=sum(1 for p in points if p.tag in ("C", "D")),
        distance_km=round(sum(leg.distance_km for leg in legs if leg.mode != "gap"), 3),
        max_speed_kmh=max(p.speed_kmh for p in points),
        legs=legs,
    )


# ---------------------------------------------------------------------------
# Analysis: time windows -> legs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Window:
    """One leg of a manual analysis: a time span, its mode and what it was."""

    start: datetime  # timezone-aware
    end: datetime
    mode: str
    title: str | None = None
    note: str | None = None
    hidden: bool = False


def parse_time(value: str) -> datetime:
    """ISO-8601 with an explicit offset (or Z). Naive times are ambiguous and rejected."""
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"Bad time: {value!r}")
    if t.tzinfo is None:
        raise ValueError(f"Time without offset: {value!r} (use e.g. 2030-03-10T09:30:00+02:00)")
    return t.astimezone(UTC)


def validate_windows(
    windows: list[Window], track_start: datetime, track_end: datetime
) -> list[str]:
    """All problems with a day's windows, as readable messages. Empty means valid."""
    errors: list[str] = []
    prev: Window | None = None
    for i, w in enumerate(windows, start=1):
        where = f"leg {i} ({w.start:%H:%M}Z)"
        if w.mode not in LEG_MODES:
            errors.append(f"{where}: unknown mode {w.mode!r}")
        if w.end <= w.start:
            errors.append(f"{where}: ends before it starts")
        if w.start < track_start - WINDOW_SLACK or w.end > track_end + WINDOW_SLACK:
            errors.append(f"{where}: outside the track ({track_start:%H:%M}–{track_end:%H:%M}Z)")
        if prev and w.start < prev.end:
            errors.append(f"{where}: overlaps or is out of order with the previous leg")
        if w.title and len(w.title) > MAX_TITLE:
            errors.append(f"{where}: title longer than {MAX_TITLE} characters")
        prev = w
    if not windows:
        errors.append("no legs")
    return errors


def _nearest(points: list[Point], times: list[datetime], t: datetime) -> Point:
    i = bisect.bisect_left(times, t)
    if i == 0:
        return points[0]
    if i == len(points):
        return points[-1]
    before, after = points[i - 1], points[i]
    return before if t - before.t <= after.t - t else after


def legs_from_windows(points: list[Point], windows: list[Window]) -> list[Leg]:
    """Build legs for validated windows; distances, speeds and lines come from the points.

    A window owns the points with start <= t < end (the last window includes its end).
    """
    times = [p.t for p in points]
    legs: list[Leg] = []
    for n, w in enumerate(windows):
        lo = bisect.bisect_left(times, w.start)
        hi = (
            bisect.bisect_right(times, w.end)
            if n == len(windows) - 1
            else bisect.bisect_left(times, w.end)
        )
        pts = points[lo:hi]
        leg = Leg(
            mode=w.mode,
            started_at=w.start,
            ended_at=w.end,
            lat=0.0,
            lon=0.0,
            title=w.title,
            note=w.note,
            is_hidden=w.hidden,
        )
        if w.mode == "gap":
            a, b = _nearest(points, times, w.start), _nearest(points, times, w.end)
            leg.lat, leg.lon = (a.lat + b.lat) / 2, (a.lon + b.lon) / 2
            leg.distance_km = round(distance_m(a, b) / 1000, 3)
            leg.lines = [[[round(a.lat, 6), round(a.lon, 6)], [round(b.lat, 6), round(b.lon, 6)]]]
        elif not pts:
            # Logger asleep for the whole window: place it where the logger last was.
            p = _nearest(points, times, w.start)
            leg.lat, leg.lon = p.lat, p.lon
        else:
            leg.lat, leg.lon = _centroid(pts)
            if w.mode != "stop":
                eps = EPS_FOOT if w.mode in FINE_MODES else EPS_VEHICLE
                leg.distance_km = round(_path_km(pts), 3)
                leg.max_speed_kmh = max(p.speed_kmh for p in pts)
                leg.lines = _lines(pts, eps)
        legs.append(leg)
    return legs
