import logging
import time
from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth.session import get_admin_user
from ..database import get_db
from ..models import City, UNCountry, User
from .models import CitySearchResponse, CitySearchResult

log = logging.getLogger(__name__)

# Nominatim rate limiting - track last request time
_nominatim_last_request: float = 0.0
_NOMINATIM_COOLDOWN = 1.0  # seconds between requests

router = APIRouter()


def _search_nominatim(
    query: str,
    country_name: str | None = None,
    fallback_country_code: str | None = None,
    country_codes: list[str] | None = None,
) -> list[CitySearchResult]:
    """Search Nominatim with rate limiting. Returns empty list on error."""
    global _nominatim_last_request

    # Enforce cooldown
    elapsed = time.time() - _nominatim_last_request
    if elapsed < _NOMINATIM_COOLDOWN:
        time.sleep(_NOMINATIM_COOLDOWN - elapsed)

    # Use structured search for better results
    # Using 'country' parameter (name) instead of 'countrycodes' for complete address data
    params: dict[str, str | int] = {
        "city": query,
        "format": "json",
        "limit": 5,
        "addressdetails": 1,
    }
    if country_name:
        # Single country - use structured search with country name
        params["country"] = country_name
    elif country_codes:
        # Multiple countries - use countrycodes filter (comma-separated ISO alpha-2)
        params["countrycodes"] = ",".join(c.lower() for c in country_codes)

    try:
        _nominatim_last_request = time.time()
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers={
                "User-Agent": "rembish.org travel tracker (hobby project)",
                "Accept-Language": "en",
            },
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        seen_names = set()
        query_lower = query.lower()

        for item in data:
            address = item.get("address", {})
            item_name = item.get("name", "")

            # Get country info - use fallback if not in address
            country = address.get("country") or country_name
            country_code = address.get("country_code", "").upper() or fallback_country_code

            # Build city name - prefer actual city fields from address
            city_name = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
            )

            # If no city field, check if the item name is a valid city
            if not city_name:
                # Skip if name contains region keywords
                if any(
                    kw in item_name.lower()
                    for kw in (
                        "emirate",
                        "region",
                        "province",
                        "state",
                        "county",
                        "district",
                        "governorate",
                    )
                ):
                    continue
                # Accept if it matches the search query (user is explicitly searching for it)
                if query_lower in item_name.lower():
                    city_name = item_name
                else:
                    continue

            if not city_name:
                continue

            # Skip duplicates
            name_key = city_name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            results.append(
                CitySearchResult(
                    name=city_name,
                    country=country,
                    country_code=country_code,
                    display_name=f"{city_name}, {country}" if country else city_name,
                    lat=float(item.get("lat", 0)),
                    lng=float(item.get("lon", 0)),
                    source="nominatim",
                )
            )
        return results
    except Exception:
        log.warning("Nominatim search failed for %r", query, exc_info=True)
        return []


@router.get("/cities-search", response_model=CitySearchResponse)
def search_cities(
    q: str = Query(..., min_length=2),
    country_codes: str | None = Query(None, description="Comma-separated ISO alpha-2 codes"),
    admin: Annotated[User | None, Depends(get_admin_user)] = None,
    db: Session = Depends(get_db),
) -> CitySearchResponse:
    """Search cities - local DB first, then Nominatim (admin only)."""
    results: list[CitySearchResult] = []
    codes = [c.strip().upper() for c in country_codes.split(",")] if country_codes else None

    # Search local City table first
    local_query = db.query(City).filter(City.name.ilike(f"%{q}%"))
    if codes:
        # Filter by country_code (ISO alpha-2), case-insensitive
        local_query = local_query.filter(City.country_code.in_(codes))
    local_cities = local_query.limit(10).all()

    for city in local_cities:
        results.append(
            CitySearchResult(
                name=city.name,
                country=city.country,
                country_code=city.country_code,
                display_name=city.display_name or f"{city.name}, {city.country}"
                if city.country
                else city.name,
                lat=city.lat,
                lng=city.lng,
                source="local",
            )
        )

    # If few local results, search Nominatim
    if len(results) < 5:
        # Convert country codes to country names for Nominatim (better results with country param)
        country_name: str | None = None
        fallback_code: str | None = None
        if codes and len(codes) == 1:
            fallback_code = codes[0]
            un_country = db.query(UNCountry).filter(UNCountry.iso_alpha2 == codes[0]).first()
            if un_country:
                country_name = un_country.name
        multi_codes = codes if codes and len(codes) > 1 else None
        nominatim_results = _search_nominatim(
            q, country_name, fallback_code, country_codes=multi_codes
        )
        # Add only non-duplicate results
        local_names = {r.name.lower() for r in results}
        for nr in nominatim_results:
            if nr.name.lower() not in local_names:
                results.append(nr)
                # Cache to local DB - only if we have country_code (for flag display)
                if nr.lat and nr.lng and nr.country_code:
                    # Check for existing by name + country_code (more reliable than country name)
                    existing = (
                        db.query(City)
                        .filter(
                            City.name == nr.name,
                            City.country_code == nr.country_code,
                        )
                        .first()
                    )
                    if not existing:
                        db.add(
                            City(
                                name=nr.name,
                                country=nr.country,
                                country_code=nr.country_code,
                                display_name=nr.display_name,
                                lat=nr.lat,
                                lng=nr.lng,
                                geocoded_at=datetime.now(UTC),
                                confidence="nominatim",
                            )
                        )
        db.commit()

    return CitySearchResponse(results=results[:10])
