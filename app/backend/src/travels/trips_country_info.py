import calendar
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..auth.session import get_trips_viewer
from ..database import get_db
from ..models import (
    TCCDestination,
    Trip,
    TripDestination,
    UNCountry,
    User,
)
from ..models.fixer import Fixer, TripFixer
from ..models.vault import TripPassport, TripTravelDoc, VaultTravelDoc, VaultVaccination
from .models import (
    CountryInfoData,
    CountryInfoTCCDestination,
    CurrencyInfo,
    DroneRules,
    HealthRequirements,
    HealthVaccination,
    MalariaInfo,
    TripCountryInfoResponse,
    TripFixerInfo,
    TripTravelDocInfo,
    WeatherInfo,
)
from .travel_advisories import get_travel_advisories
from .trips_external import (
    _fetch_currency_rates,
    _fetch_holidays_for_country,
    _fetch_sunrise_sunset,
    _fetch_weather,
    _get_currency_name,
)

# Health requirements data: loaded once from static JSON
_health_data: dict[str, dict] = {}
_health_data_path = Path(__file__).parent.parent / "data" / "health_requirements.json"
if _health_data_path.exists():
    with open(_health_data_path) as _f:
        _raw = json.load(_f)
        for _c in _raw.get("countries", []):
            _health_data[_c["country_code"]] = _c

# Drone rules: loaded once from static JSON
_drone_rules: dict[str, dict] = {}
_drone_rules_path = Path(__file__).parent.parent / "data" / "drone_rules.json"
if _drone_rules_path.exists():
    with open(_drone_rules_path) as _f:
        _raw_dr = json.load(_f)
        for _c in _raw_dr.get("countries", []):
            _drone_rules[_c["country_code"]] = _c

# Czech socket types for adapter comparison
_CZ_SOCKETS = {"C", "E"}

log = logging.getLogger(__name__)

router = APIRouter()


def _needs_adapter(socket_types: str | None) -> bool | None:
    """Check if country needs a power adapter (compared to Czech C/E)."""
    if not socket_types:
        return None
    country_sockets = {s.strip() for s in socket_types.split(",")}
    # Adapter not needed if country supports C or E (Czech standard)
    return not bool(country_sockets & _CZ_SOCKETS)


def _compute_timezone_offset(tz_name: str, ref_date: date) -> float | None:
    """Compute timezone offset from CET in hours."""
    try:
        country_tz = ZoneInfo(tz_name)
        cet_tz = ZoneInfo("Europe/Prague")
        ref_dt = datetime(ref_date.year, ref_date.month, ref_date.day, 12, 0)
        country_offset = ref_dt.replace(tzinfo=country_tz).utcoffset()
        cet_offset = ref_dt.replace(tzinfo=cet_tz).utcoffset()
        if country_offset is None or cet_offset is None:
            return None
        diff_seconds = (country_offset - cet_offset).total_seconds()
        return diff_seconds / 3600
    except Exception:
        return None


def _vaccine_matches(cdc_name: str, user_names: set[str]) -> bool:
    """Check if a CDC vaccine name matches any user vaccination (fuzzy).

    Handles combined vaccines: user's "Hepatitis A+B" covers both
    CDC's "Hepatitis A" and "Hepatitis B".
    """
    cdc_lower = cdc_name.lower()
    # Strip parenthetical suffixes: "Polio (booster)" → "polio"
    base = cdc_lower.split("(")[0].strip()
    for uname in user_names:
        u = uname.lower()
        if u == cdc_lower or u == base or cdc_lower.startswith(u) or u.startswith(base):
            return True
        # Combined vaccines: split on +/& and check each part
        # e.g. "hepatitis a+b" → ["hepatitis a", "hepatitis b"]
        for sep in ("+", "&", " and "):
            if sep in u:
                parts = [p.strip() for p in u.split(sep)]
                # Expand shorthand: ["hepatitis a", "b"] → ["hepatitis a", "hepatitis b"]
                prefix = ""
                expanded = []
                for part in parts:
                    if " " in part:
                        prefix = part.rsplit(" ", 1)[0]
                        expanded.append(part)
                    elif prefix:
                        expanded.append(f"{prefix} {part}")
                    else:
                        expanded.append(part)
                if base in expanded or cdc_lower in expanded:
                    return True
    return False


def _get_health_requirements(
    iso_alpha2: str, user_vaccine_names: set[str] | None = None
) -> HealthRequirements | None:
    """Look up health requirements for a country by ISO alpha-2 code."""
    entry = _health_data.get(iso_alpha2)
    if not entry:
        return None

    names = user_vaccine_names or set()
    vax = entry.get("vaccinations", {})
    required = [
        HealthVaccination(
            vaccine=v["vaccine"],
            priority=v.get("priority", "required"),
            notes=v.get("notes"),
            covered=_vaccine_matches(v["vaccine"], names),
        )
        for v in vax.get("required", [])
    ]
    recommended = [
        HealthVaccination(
            vaccine=v["vaccine"],
            priority=v.get("priority", "recommended"),
            notes=v.get("notes"),
            covered=_vaccine_matches(v["vaccine"], names),
        )
        for v in vax.get("recommended", [])
    ]
    routine = vax.get("routine", [])

    malaria = None
    mal_data = entry.get("malaria")
    if mal_data:
        malaria = MalariaInfo(
            risk=mal_data.get("risk", False),
            areas=mal_data.get("areas"),
            species=mal_data.get("species"),
            prophylaxis=mal_data.get("prophylaxis") or [],
            drug_resistance=mal_data.get("drug_resistance") or [],
        )

    return HealthRequirements(
        vaccinations_required=required,
        vaccinations_recommended=recommended,
        vaccinations_routine=routine,
        malaria=malaria,
        other_risks=entry.get("other_risks", []),
    )


def _get_drone_rules(iso_alpha2: str) -> DroneRules | None:
    """Look up drone rules for a country by ISO alpha-2 code."""
    entry = _drone_rules.get(iso_alpha2)
    if not entry:
        return None
    return DroneRules(
        status=entry["status"],
        max_altitude_m=entry.get("max_altitude_m"),
        registration_required=entry.get("registration_required"),
        registration_weight_g=entry.get("registration_weight_g"),
        license_required=entry.get("license_required"),
        insurance_required=entry.get("insurance_required"),
        sub_250g_notes=entry.get("sub_250g_notes"),
        import_restrictions=entry.get("import_restrictions"),
        notes=entry.get("notes"),
        authority=entry.get("authority"),
        authority_url=entry.get("authority_url"),
        source_url=entry.get("source_url"),
    )


def get_trip_travel_docs(trip: Trip, trip_id: int, db: Session) -> dict[str, list[VaultTravelDoc]]:
    """Return travel docs for a trip, grouped by country code (uppercase).

    Includes explicitly assigned docs + auto-matched docs by country code.
    """
    result: dict[str, list[VaultTravelDoc]] = {}
    seen_doc_ids: set[int] = set()

    # Get the trip's assigned passport (to filter visa-passport linkage)
    trip_passport = db.query(TripPassport).filter(TripPassport.trip_id == trip_id).first()
    trip_passport_id = trip_passport.document_id if trip_passport else None

    # 1. Explicitly assigned to this trip
    ttd_rows = (
        db.query(VaultTravelDoc)
        .join(TripTravelDoc, TripTravelDoc.travel_doc_id == VaultTravelDoc.id)
        .filter(TripTravelDoc.trip_id == trip_id)
        .all()
    )
    for vtd in ttd_rows:
        cc = (vtd.country_code or "").upper()
        if cc:
            result.setdefault(cc, []).append(vtd)
            seen_doc_ids.add(vtd.id)

    # 2. Auto-match: docs matching trip's destination countries
    today = date.today()
    trip_is_past = trip.end_date is not None and trip.end_date < today
    validity_cutoff = trip.start_date if trip_is_past else today

    # Single-entry visas assigned to a DIFFERENT completed trip are considered used
    used_single_ids: set[int] = {
        row[0]
        for row in db.query(VaultTravelDoc.id)
        .join(TripTravelDoc, TripTravelDoc.travel_doc_id == VaultTravelDoc.id)
        .join(Trip, Trip.id == TripTravelDoc.trip_id)
        .filter(
            VaultTravelDoc.entry_type == "single",
            Trip.end_date.isnot(None),
            Trip.end_date < today,
            Trip.id != trip_id,
        )
        .all()
    }

    country_docs = (
        db.query(VaultTravelDoc)
        .filter(
            VaultTravelDoc.country_code.isnot(None),
            (VaultTravelDoc.valid_until.is_(None))
            | (VaultTravelDoc.valid_until >= validity_cutoff),
        )
        .all()
    )
    for vtd in country_docs:
        if vtd.id in seen_doc_ids:
            continue
        if vtd.id in used_single_ids:
            continue
        if vtd.document_id and trip_passport_id and vtd.document_id != trip_passport_id:
            continue
        cc = (vtd.country_code or "").upper()
        if cc:
            result.setdefault(cc, []).append(vtd)

    return result


def get_trip_vaccination_needs(
    trip: Trip, db: Session, user_id: int
) -> list[tuple[str, str, bool]]:
    """Return vaccination needs for all trip countries.

    Returns list of (vaccine_name, priority, covered) tuples.
    """
    user_vax_names: set[str] = set()
    vax_records = (
        db.query(VaultVaccination.vaccine_name).filter(VaultVaccination.user_id == user_id).all()
    )
    for (name,) in vax_records:
        user_vax_names.add(name)

    seen_vaccines: set[str] = set()
    needs: list[tuple[str, str, bool]] = []

    for td in trip.destinations:
        un = td.tcc_destination.un_country
        if not un:
            continue
        health = _get_health_requirements(un.iso_alpha2, user_vax_names)
        if not health:
            continue
        for v in health.vaccinations_required:
            key = v.vaccine.lower()
            if key not in seen_vaccines:
                seen_vaccines.add(key)
                needs.append((v.vaccine, "required", v.covered))
        for v in health.vaccinations_recommended:
            key = v.vaccine.lower()
            if key not in seen_vaccines:
                seen_vaccines.add(key)
                needs.append((v.vaccine, "recommended", v.covered))

    return needs


@router.get("/trips/{trip_id}/country-info", response_model=TripCountryInfoResponse)
def get_trip_country_info(
    trip_id: int,
    admin: Annotated[User, Depends(get_trips_viewer)],
    db: Session = Depends(get_db),
) -> TripCountryInfoResponse:
    """Get aggregated country reference data for a trip's destinations (admin only)."""
    trip = (
        db.query(Trip)
        .options(
            joinedload(Trip.destinations)
            .joinedload(TripDestination.tcc_destination)
            .joinedload(TCCDestination.un_country),
        )
        .filter(Trip.id == trip_id)
        .first()
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Get admin's vaccination records for coverage matching
    user_vax_names: set[str] = set()
    vax_records = (
        db.query(VaultVaccination.vaccine_name).filter(VaultVaccination.user_id == admin.id).all()
    )
    for (name,) in vax_records:
        user_vax_names.add(name)

    # Query travel documents using shared helper
    trip_travel_docs = get_trip_travel_docs(trip, trip_id, db)

    # Auto-seed fixers on first info view, then manual management
    if not trip.fixers_synced:
        # Collect trip's destination country codes
        dest_codes: set[str] = set()
        for td in trip.destinations:
            un = td.tcc_destination.un_country
            if un:
                dest_codes.add(un.iso_alpha2)

        # Find fixers matching any destination country
        if dest_codes:
            from ..models.fixer import FixerCountry

            matching = (
                db.query(Fixer)
                .join(Fixer.countries)
                .filter(FixerCountry.country_code.in_(dest_codes))
                .all()
            )
            existing_ids = {
                row[0]
                for row in db.query(TripFixer.fixer_id).filter(TripFixer.trip_id == trip_id).all()
            }
            for fixer in matching:
                if fixer.id not in existing_ids:
                    db.add(TripFixer(trip_id=trip_id, fixer_id=fixer.id))

        trip.fixers_synced = True
        db.commit()

    # Query fixers: assigned (in trip_fixers) + available (matching but not assigned)
    trip_fixers: dict[str, list[tuple[Fixer, bool]]] = {}
    assigned_fixer_ids: set[int] = set()

    # Assigned fixers
    assigned = (
        db.query(Fixer)
        .join(TripFixer, TripFixer.fixer_id == Fixer.id)
        .filter(TripFixer.trip_id == trip_id)
        .all()
    )
    for fixer in assigned:
        assigned_fixer_ids.add(fixer.id)
        for fc in fixer.countries:
            cc = fc.country_code.upper()
            trip_fixers.setdefault(cc, []).append((fixer, True))

    # Available fixers (matching by country but not assigned)
    all_fixers = db.query(Fixer).join(Fixer.countries).all()
    for fixer in all_fixers:
        if fixer.id in assigned_fixer_ids:
            continue
        for fc in fixer.countries:
            cc = fc.country_code.upper()
            trip_fixers.setdefault(cc, []).append((fixer, False))

    # Group TCC destinations by UN country
    # Key: un_country_id (or negative tcc_id for orphans)
    grouped: dict[int, tuple[UNCountry | None, list[tuple[str, bool]]]] = {}
    for td in trip.destinations:
        tcc = td.tcc_destination
        un = tcc.un_country
        key = un.id if un else -tcc.id
        if key not in grouped:
            grouped[key] = (un, [])
        grouped[key][1].append((tcc.name, td.is_partial))

    trip_start = trip.start_date
    trip_end = trip.end_date or trip.start_date
    # Use mid-trip date for weather month
    mid_trip = trip_start + (trip_end - trip_start) / 2
    trip_month = mid_trip.month

    countries: list[CountryInfoData] = []
    for _key, (un_country, tcc_dests) in sorted(
        grouped.items(),
        key=lambda x: x[1][0].name if x[1][0] else x[1][1][0][0],
    ):
        if un_country:
            country_name = un_country.name
            iso = un_country.iso_alpha2

            # Currency
            currency = None
            if un_country.currency_code:
                rates = _fetch_currency_rates(un_country.currency_code)
                currency = CurrencyInfo(
                    code=un_country.currency_code,
                    name=_get_currency_name(un_country.currency_code),
                    rates=rates,
                )

            # Weather
            weather = None
            if un_country.capital_lat is not None and un_country.capital_lng is not None:
                w = _fetch_weather(un_country.capital_lat, un_country.capital_lng, trip_month)
                rainy_days_val = w.get("rainy_days")
                weather = WeatherInfo(
                    avg_temp_c=w.get("avg_temp_c"),
                    min_temp_c=w.get("min_temp_c"),
                    max_temp_c=w.get("max_temp_c"),
                    avg_precipitation_mm=w.get("avg_precipitation_mm"),
                    rainy_days=int(rainy_days_val) if rainy_days_val is not None else None,
                    month=calendar.month_name[trip_month],
                )

            # Timezone
            tz_offset = None
            if un_country.timezone:
                tz_offset = _compute_timezone_offset(un_country.timezone, trip_start)

            # Holidays
            holidays = _fetch_holidays_for_country(iso, trip_start, trip_end)

            # Sunrise/sunset for mid-trip date
            sunrise_sunset = None
            if un_country.capital_lat is not None and un_country.capital_lng is not None:
                sunrise_sunset = _fetch_sunrise_sunset(
                    un_country.capital_lat,
                    un_country.capital_lng,
                    mid_trip,
                    tz_offset,
                )

            countries.append(
                CountryInfoData(
                    country_name=country_name,
                    iso_alpha2=iso,
                    tcc_destinations=[
                        CountryInfoTCCDestination(name=n, is_partial=p) for n, p in tcc_dests
                    ],
                    socket_types=un_country.socket_types,
                    voltage=un_country.voltage,
                    phone_code=un_country.phone_code,
                    driving_side=un_country.driving_side,
                    emergency_number=un_country.emergency_number,
                    tap_water=un_country.tap_water,
                    currency=currency,
                    weather=weather,
                    timezone_offset_hours=tz_offset,
                    holidays=holidays,
                    languages=un_country.languages,
                    tipping=un_country.tipping,
                    speed_limits=un_country.speed_limits,
                    visa_free_days=un_country.visa_free_days,
                    eu_roaming=un_country.eu_roaming,
                    adapter_needed=_needs_adapter(un_country.socket_types),
                    sunrise_sunset=sunrise_sunset,
                    health=_get_health_requirements(iso, user_vax_names),
                    drone_rules=_get_drone_rules(iso),
                    advisories=get_travel_advisories(iso, trip_start, trip_end),
                    travel_docs=[
                        TripTravelDocInfo(
                            id=vtd.id,
                            doc_type=vtd.doc_type,
                            label=vtd.label,
                            valid_until=vtd.valid_until.isoformat() if vtd.valid_until else None,
                            entry_type=vtd.entry_type,
                            passport_label=vtd.passport.label if vtd.passport else None,
                            expires_before_trip=bool(
                                vtd.valid_until and vtd.valid_until < trip_end
                            ),
                            has_files=len(vtd.files) > 0 if vtd.files else False,
                        )
                        for vtd in trip_travel_docs.get(iso, [])
                    ],
                    fixers=[
                        TripFixerInfo(
                            id=f.id,
                            name=f.name,
                            type=f.type,
                            whatsapp=f.whatsapp,
                            phone=f.phone,
                            rating=f.rating,
                            is_assigned=assigned,
                        )
                        for f, assigned in trip_fixers.get(iso, [])
                    ],
                )
            )
        else:
            # Orphan TCC destination (e.g., Kosovo) — minimal card
            name = tcc_dests[0][0] if tcc_dests else "Unknown"
            countries.append(
                CountryInfoData(
                    country_name=name,
                    iso_alpha2="",
                    tcc_destinations=[
                        CountryInfoTCCDestination(name=n, is_partial=p) for n, p in tcc_dests
                    ],
                    socket_types=None,
                    voltage=None,
                    phone_code=None,
                    driving_side=None,
                    emergency_number=None,
                    tap_water=None,
                    currency=None,
                    weather=None,
                    timezone_offset_hours=None,
                    holidays=[],
                    languages=None,
                    tipping=None,
                    speed_limits=None,
                    visa_free_days=None,
                    eu_roaming=None,
                    adapter_needed=None,
                    sunrise_sunset=None,
                )
            )

    return TripCountryInfoResponse(countries=countries)
