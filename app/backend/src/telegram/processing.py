"""DJI flight record processing — parse, extract, and store drone flights."""

import math
import re
from datetime import date, datetime

import reverse_geocode
from pydjirecord import DJILog, FrameDetails
from sqlalchemy.orm import Session

from ..config import settings
from ..log_config import get_logger
from ..models import Battery, Drone, DroneFlight, Trip, UNCountry

log = get_logger(__name__)

# Map DroneType enum names to (model, name, serial_number)
DRONE_MODELS: dict[str, tuple[str, str, str]] = {
    "MAVIC_AIR2": ("Mavic Air 2", "air2.rembish.org", "1WNBH56002008D"),
    "MINI4_PRO": ("Mini 4 Pro", "m4p.rembish.org", "1581F6Z9C23CP003"),
}

RDP_EPSILON = 0.00001  # ~1m at equator


# ---------------------------------------------------------------------------
# RDP simplification (pure math, copied from seed_drone_flights.py)
# ---------------------------------------------------------------------------


def _perpendicular_distance(point: list[float], start: list[float], end: list[float]) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    mag_sq = dx * dx + dy * dy
    if mag_sq == 0.0:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    t = max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / mag_sq))
    proj_x = start[0] + t * dx
    proj_y = start[1] + t * dy
    return math.hypot(point[0] - proj_x, point[1] - proj_y)


def _rdp_simplify(coords: list[list[float]], epsilon: float) -> list[list[float]]:
    if len(coords) <= 2:
        return coords
    max_dist = 0.0
    max_idx = 0
    for i in range(1, len(coords) - 1):
        d = _perpendicular_distance(coords[i], coords[0], coords[-1])
        if d > max_dist:
            max_dist = d
            max_idx = i
    if max_dist > epsilon:
        left = _rdp_simplify(coords[: max_idx + 1], epsilon)
        right = _rdp_simplify(coords[max_idx:], epsilon)
        return left[:-1] + right
    return [coords[0], coords[-1]]


# ---------------------------------------------------------------------------
# Trip matching (copied from seed_drone_flights.py)
# ---------------------------------------------------------------------------


def _find_trip(db: Session, flight_date: date) -> Trip | None:
    """Find the most specific trip overlapping the flight date (bounded first)."""
    trip = (
        db.query(Trip)
        .filter(
            Trip.start_date <= flight_date,
            Trip.end_date >= flight_date,
            Trip.end_date.isnot(None),
        )
        .order_by(Trip.end_date - Trip.start_date)
        .first()
    )
    if trip:
        return trip
    return db.query(Trip).filter(Trip.start_date <= flight_date, Trip.end_date.is_(None)).first()


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------


def process_flight_record(data: bytes, filename: str, db: Session, *, is_test: bool = False) -> str:
    """Parse a DJI flight record and insert into drone_flights.

    Returns a formatted summary string for the Telegram reply.
    Raises on parse errors (caller should catch and reply with error).
    """
    # 1. Parse
    dji_log = DJILog.from_bytes(data)

    api_key = settings.dji_api_key
    keychains = dji_log.fetch_keychains(api_key) if api_key and dji_log.version >= 13 else None
    frames = dji_log.frames(keychains)

    # 2. Extract metadata
    fd = FrameDetails.from_details(dji_log.details, frames)

    lat = round(fd.latitude, 6)
    lon = round(fd.longitude, 6)
    duration_sec = round(fd.total_time, 1)
    distance_km = round(fd.total_distance / 1000.0, 3)
    max_speed_ms = round(fd.max_horizontal_speed, 1)
    photos = fd.photo_num
    video_sec = round(fd.video_time)

    # Drone type from first OSD frame
    drone_type_name = ""
    for frame in frames:
        if frame.osd.drone_type is not None:
            drone_type_name = frame.osd.drone_type.name
            break

    # Takeoff time from first frame's custom.date_time
    takeoff_time: datetime | None = None
    for frame in frames:
        dt = frame.custom.date_time
        if dt.year > 1970:
            takeoff_time = dt
            break

    # Date from filename: DJIFlightRecord_YYYY-MM-DD_[HH-MM-SS].txt
    flight_date: date | None = None
    m = re.match(r"(?:DJI)?FlightRecord_(\d{4}-\d{2}-\d{2})", filename)
    if m:
        flight_date = date.fromisoformat(m.group(1))
    elif takeoff_time:
        flight_date = takeoff_time.date()

    if flight_date is None:
        return "Could not determine flight date from filename or record data."

    # source_file for dedup (use original filename without extension)
    source_file = re.sub(r"\.txt$", "", filename, flags=re.IGNORECASE)

    # 3. Dedup — by exact source_file, then by date+time from filename
    existing = db.query(DroneFlight).filter(DroneFlight.source_file == source_file).first()
    if existing:
        return f"Already imported: {filename} (flight #{existing.id})"
    # Filename contains local time: (DJI)FlightRecord_YYYY-MM-DD_[HH-MM-SS].txt
    # Original bulk import stored source_file as YYYY-MM-DD_HHMMSS_DRONE_TYPE
    time_match = re.search(r"(\d{4}-\d{2}-\d{2})_\[(\d{2})-(\d{2})-(\d{2})\]", filename)
    if time_match:
        date_str = time_match.group(1)
        time_prefix = f"{date_str}_{time_match.group(2)}{time_match.group(3)}{time_match.group(4)}"
        existing = (
            db.query(DroneFlight).filter(DroneFlight.source_file.like(f"{time_prefix}%")).first()
        )
        if existing:
            return f"Already imported: {filename} (flight #{existing.id}, matched by date+time)"

    # 4. Skip flights without GPS
    if lat == 0.0 and lon == 0.0:
        return f"Skipped {filename}: no GPS data (0/0 coordinates)."

    # 5. Flight path — extract from frames, simplify with RDP
    coords: list[list[float]] = []
    for frame in frames:
        if frame.osd.latitude != 0.0 or frame.osd.longitude != 0.0:
            coords.append([frame.osd.longitude, frame.osd.latitude])
    flight_path: list[list[float]] | None = None
    if len(coords) >= 2:
        simplified = _rdp_simplify(coords, RDP_EPSILON)
        if len(simplified) >= 2:
            flight_path = [[round(c[0], 6), round(c[1], 6)] for c in simplified]

    # 6. Reverse geocode
    geo_results = reverse_geocode.search([(lat, lon)])
    country = geo_results[0].get("country_code", "") if geo_results else ""
    city = geo_results[0].get("city", "") if geo_results else ""

    # 7. Find or create drone
    drone_id: int | None = None
    if drone_type_name and drone_type_name in DRONE_MODELS:
        model, name, serial = DRONE_MODELS[drone_type_name]
        drone = db.query(Drone).filter(Drone.name == name).first()
        if not drone:
            drone = Drone(name=name, model=model, serial_number=serial)
            db.add(drone)
            db.flush()
        drone_id = drone.id

    # 8. Battery identification and telemetry
    battery_id: int | None = None
    battery_charge_start: int | None = None
    battery_charge_end: int | None = None
    battery_health_pct: int | None = None
    battery_cycles: int | None = None
    battery_temp_max: float | None = None
    battery_sn: str | None = getattr(dji_log.details, "battery_sn", None)

    if battery_sn:
        battery = db.query(Battery).filter(Battery.serial_number == battery_sn).first()
        if not battery:
            # Auto-create battery from first frame data
            design_cap: int | None = None
            cell_count: int | None = None
            if frames:
                first_bat = frames[0].battery
                if first_bat.design_capacity > 0:
                    design_cap = first_bat.design_capacity
                if first_bat.cell_voltages:
                    cell_count = len(first_bat.cell_voltages)
            battery = Battery(
                drone_id=drone_id,
                serial_number=battery_sn,
                design_capacity_mah=design_cap,
                cell_count=cell_count,
            )
            db.add(battery)
            db.flush()
        elif battery.drone_id is None and drone_id is not None:
            # Auto-assign battery to drone if not yet assigned
            battery.drone_id = drone_id
        battery_id = battery.id

    # Extract battery telemetry from frames
    if frames:
        first_bat = frames[0].battery
        last_bat = frames[-1].battery
        if first_bat.charge_level > 0:
            battery_charge_start = first_bat.charge_level
        if last_bat.charge_level > 0:
            battery_charge_end = last_bat.charge_level
        if last_bat.design_capacity > 0 and last_bat.full_capacity > 0:
            battery_health_pct = round(last_bat.full_capacity / last_bat.design_capacity * 100)
        if last_bat.number_of_discharges > 0:
            battery_cycles = last_bat.number_of_discharges
        # Max temperature across all frames
        temps = [f.battery.temperature for f in frames if f.battery.temperature > 0]
        if temps:
            battery_temp_max = round(max(temps), 1)

    # 9. Anomaly extraction
    anomaly_severity: str | None = None
    anomaly_actions: str | None = None
    anomaly_label = ""
    if fd.anomaly is not None:
        severity_name = fd.anomaly.severity.name  # GREEN, AMBER, RED
        if severity_name != "GREEN":
            anomaly_severity = severity_name
            actions_list = [a.name.replace("_", " ").title() for a in fd.anomaly.actions]
            if actions_list:
                anomaly_actions = ",".join(a.name for a in fd.anomaly.actions)
            if severity_name == "RED":
                anomaly_label = "RED"
                actions_display = ", ".join(actions_list)
                if actions_display:
                    anomaly_label += f" ({actions_display})"
            elif severity_name == "AMBER":
                anomaly_label = "AMBER"

    # 10. Trip matching (skip for CZ — home country)
    trip_id: int | None = None
    if country != "CZ":
        trip = _find_trip(db, flight_date)
        trip_id = trip.id if trip else None

    # 11. Auto-hide very short flights (<30s)
    is_hidden = duration_sec < 30

    # 12. Insert
    flight = DroneFlight(
        drone_id=drone_id,
        trip_id=trip_id,
        battery_id=battery_id,
        flight_date=flight_date,
        takeoff_time=takeoff_time,
        latitude=lat,
        longitude=lon,
        duration_sec=duration_sec,
        distance_km=distance_km,
        max_speed_ms=max_speed_ms,
        photos=photos,
        video_sec=video_sec,
        country=country,
        city=city,
        is_hidden=is_hidden,
        source_file=source_file,
        flight_path=flight_path,
        anomaly_severity=anomaly_severity,
        anomaly_actions=anomaly_actions,
        battery_charge_start=battery_charge_start,
        battery_charge_end=battery_charge_end,
        battery_health_pct=battery_health_pct,
        battery_cycles=battery_cycles,
        battery_temp_max=battery_temp_max,
        is_test=is_test,
    )
    db.add(flight)

    # Update un_countries.drone_flown
    if country:
        uc = db.query(UNCountry).filter(UNCountry.iso_alpha2 == country).first()
        if uc and not uc.drone_flown:
            uc.drone_flown = True

    db.commit()

    # 13. Build reply
    battery_pct = battery_charge_start
    battery_health: str = ""
    if battery_health_pct is not None:
        battery_health = f"{battery_health_pct}%"
    if frames:
        last_bat = frames[-1].battery
        if last_bat.lifetime_remaining > 0:
            battery_health += f" ({last_bat.lifetime_remaining} cycles left)"

    parts = [f"Flight imported: #{flight.id}"]
    parts.append(f"Date: {flight_date}")
    if takeoff_time:
        parts.append(f"Time: {takeoff_time.strftime('%H:%M:%S')}")
    if city and country:
        parts.append(f"Location: {city}, {country}")
    elif country:
        parts.append(f"Country: {country}")
    parts.append(f"Duration: {int(duration_sec)}s")
    if distance_km > 0:
        parts.append(f"Distance: {distance_km} km")
    if photos > 0:
        parts.append(f"Photos: {photos}")
    if video_sec > 0:
        mins, secs = divmod(video_sec, 60)
        parts.append(f"Video: {mins}m{secs}s" if mins else f"Video: {secs}s")
    if drone_type_name:
        model_name = DRONE_MODELS.get(drone_type_name, (drone_type_name,))[0]
        parts.append(f"Drone: {model_name}")
    if battery_sn:
        parts.append(f"Battery S/N: {battery_sn}")
    if battery_pct is not None:
        bat_str = f"Battery: {battery_pct}%"
        if battery_health:
            bat_str += f" (health: {battery_health})"
        parts.append(bat_str)
    if anomaly_label:
        parts.append(f"Anomaly: {anomaly_label}")
    if is_hidden:
        parts.append("(auto-hidden: <30s)")
    if trip_id:
        parts.append(f"Matched trip #{trip_id}")
    if flight_path:
        parts.append(f"Path: {len(flight_path)} points")

    return "\n".join(parts)
