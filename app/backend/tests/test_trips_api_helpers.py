"""Unit tests for trips.py external API helper functions.

Tests the currency, weather, sunrise/sunset, and holiday fetcher functions
with mocked httpx to cover the external API integration code.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import httpx


# --- Currency fetching ---


@patch("httpx.get")
def test_fetch_frankfurter_success(mock_get: MagicMock) -> None:
    from src.travels.trips import _currency_cache, _fetch_frankfurter

    _currency_cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"rates": {"CZK": 25.5, "USD": 1.08}}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = _fetch_frankfurter("EUR")
    assert result is not None
    assert result["CZK"] == 25.5
    assert result["USD"] == 1.08
    assert result["EUR"] == 1.0  # self-rate added


@patch("httpx.get", side_effect=httpx.ConnectError("timeout"))
def test_fetch_frankfurter_failure(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_frankfurter

    result = _fetch_frankfurter("EUR")
    assert result is None


@patch("httpx.get")
def test_fetch_open_er_success(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_open_er

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": "success",
        "rates": {"CZK": 25.0, "EUR": 1.1, "USD": 1.0, "JPY": 150.0},
    }
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = _fetch_open_er("USD")
    assert result is not None
    assert "CZK" in result
    assert "EUR" in result
    assert "USD" in result
    assert "JPY" not in result  # not in target currencies


@patch("httpx.get")
def test_fetch_open_er_failure(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_open_er

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": "error"}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = _fetch_open_er("XYZ")
    assert result is None


@patch("httpx.get", side_effect=Exception("network"))
def test_fetch_open_er_exception(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_open_er

    result = _fetch_open_er("XYZ")
    assert result is None


def test_fetch_currency_rates_ecb_supported() -> None:
    """ECB-supported currency uses Frankfurter, falls back to open.er on failure."""
    from src.travels.trips import _currency_cache, _fetch_currency_rates

    _currency_cache.clear()

    with patch("src.travels.trips_external._fetch_frankfurter", return_value={"EUR": 1.0, "CZK": 25.5}):
        result = _fetch_currency_rates("EUR")
        assert result is not None
        assert result["CZK"] == 25.5


def test_fetch_currency_rates_non_ecb() -> None:
    """Non-ECB currency skips Frankfurter, uses open.er directly."""
    from src.travels.trips import _currency_cache, _fetch_currency_rates

    _currency_cache.clear()

    with patch("src.travels.trips_external._fetch_frankfurter") as mock_frank:
        with patch(
            "src.travels.trips_external._fetch_open_er",
            return_value={"MAD": 1.0, "EUR": 0.09, "CZK": 2.3},
        ):
            result = _fetch_currency_rates("MAD")
            mock_frank.assert_not_called()  # MAD is not ECB
            assert result is not None
            assert result["MAD"] == 1.0


def test_fetch_currency_rates_fallback() -> None:
    """When Frankfurter fails, falls back to open.er."""
    from src.travels.trips import _currency_cache, _fetch_currency_rates

    _currency_cache.clear()

    with patch("src.travels.trips_external._fetch_frankfurter", return_value=None):
        with patch(
            "src.travels.trips_external._fetch_open_er",
            return_value={"GBP": 1.0, "EUR": 1.17, "CZK": 29.0},
        ):
            result = _fetch_currency_rates("GBP")
            assert result is not None
            assert result["EUR"] == 1.17


def test_fetch_currency_rates_cached() -> None:
    """Second call returns cached result."""
    from src.travels.trips import _currency_cache, _fetch_currency_rates

    _currency_cache.clear()

    with patch("src.travels.trips_external._fetch_frankfurter", return_value={"EUR": 1.0}) as mock_frank:
        _fetch_currency_rates("EUR")
        _fetch_currency_rates("EUR")  # should be cached
        mock_frank.assert_called_once()


# --- Weather fetching ---


@patch("httpx.get")
def test_fetch_weather_success(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_weather, _weather_cache

    _weather_cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "daily": {
            "temperature_2m_mean": [15.0, 16.0, 14.0],
            "temperature_2m_min": [8.0, 9.0, 7.0],
            "temperature_2m_max": [22.0, 23.0, 21.0],
            "precipitation_sum": [0.0, 3.0, 0.0],
        }
    }
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = _fetch_weather(50.0, 14.0, 3)
    assert result["avg_temp_c"] == 15.0
    assert result["min_temp_c"] == 8.0
    assert result["max_temp_c"] == 22.0
    assert result["rainy_days"] == 1  # only 3.0 > 0.5


@patch("httpx.get", side_effect=Exception("error"))
def test_fetch_weather_failure(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_weather, _weather_cache

    _weather_cache.clear()

    result = _fetch_weather(50.0, 14.0, 6)
    assert result["avg_temp_c"] is None
    assert result["rainy_days"] is None


def test_fetch_weather_cached() -> None:
    from src.travels.trips import _fetch_weather, _weather_cache

    _weather_cache.clear()

    with patch("httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "daily": {
                "temperature_2m_mean": [10.0],
                "temperature_2m_min": [5.0],
                "temperature_2m_max": [15.0],
                "precipitation_sum": [0.0],
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        _fetch_weather(50.0, 14.0, 1)
        _fetch_weather(50.0, 14.0, 1)
        mock_get.assert_called_once()


# --- Sunrise/sunset ---


@patch("httpx.get")
def test_fetch_sunrise_sunset_success(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_sunrise_sunset, _sunrise_cache

    _sunrise_cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "OK",
        "results": {
            "sunrise": "2026-03-10T06:00:00+00:00",
            "sunset": "2026-03-10T18:00:00+00:00",
            "day_length": 43200,
        },
    }
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = _fetch_sunrise_sunset(50.0, 14.0, date(2026, 3, 10), 0.0)
    assert result is not None
    assert ":" in result.sunrise
    assert ":" in result.sunset
    assert result.day_length_hours == 12.0


@patch("httpx.get")
def test_fetch_sunrise_sunset_not_ok(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_sunrise_sunset, _sunrise_cache

    _sunrise_cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "INVALID_DATE"}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = _fetch_sunrise_sunset(50.0, 14.0, date(2026, 3, 10), None)
    assert result is None


@patch("httpx.get", side_effect=Exception("error"))
def test_fetch_sunrise_sunset_failure(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_sunrise_sunset, _sunrise_cache

    _sunrise_cache.clear()

    result = _fetch_sunrise_sunset(50.0, 14.0, date(2026, 3, 15), 0.0)
    assert result is None


# --- Holiday fetching ---


@patch("httpx.get")
def test_fetch_holidays_raw_success(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_holidays_raw, _holidays_cache

    _holidays_cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"date": "2026-01-01", "name": "New Year", "localName": "Nový rok"},
        {"date": "2026-12-25", "name": "Christmas"},
    ]
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = _fetch_holidays_raw(2026, "CZ")
    assert len(result) == 2
    assert result[0]["name"] == "New Year"


@patch("httpx.get")
def test_fetch_holidays_raw_204(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_holidays_raw, _holidays_cache

    _holidays_cache.clear()

    mock_resp = MagicMock()
    mock_resp.status_code = 204
    mock_get.return_value = mock_resp

    result = _fetch_holidays_raw(2026, "XX")
    assert result == []


@patch("httpx.get", side_effect=Exception("error"))
def test_fetch_holidays_raw_failure(mock_get: MagicMock) -> None:
    from src.travels.trips import _fetch_holidays_raw, _holidays_cache

    _holidays_cache.clear()

    result = _fetch_holidays_raw(2026, "CZ")
    assert result == []


def test_fetch_holidays_for_country() -> None:
    from src.travels.trips import _fetch_holidays_for_country, _holidays_cache

    _holidays_cache.clear()

    with patch(
        "src.travels.trips_external._fetch_holidays_raw",
        return_value=[
            {"date": "2026-03-05", "name": "Holiday A"},
            {"date": "2026-03-15", "name": "Holiday B"},
            {"date": "2026-04-01", "name": "Outside Range"},
        ],
    ):
        result = _fetch_holidays_for_country("CZ", date(2026, 3, 1), date(2026, 3, 20))
        assert len(result) == 2
        assert result[0].name == "Holiday A"
        assert result[1].name == "Holiday B"


def test_fetch_holidays_for_country_cached() -> None:
    """Uses cache when available."""
    from src.travels.trips import _fetch_holidays_for_country, _holidays_cache

    _holidays_cache.clear()
    # Pre-populate cache
    _holidays_cache[(2026, "DE")] = [
        {"date": "2026-06-01", "name": "Cached Holiday"},
    ]

    result = _fetch_holidays_for_country("DE", date(2026, 5, 1), date(2026, 7, 1))
    assert len(result) == 1
    assert result[0].name == "Cached Holiday"


# --- Country info endpoint with more external API coverage ---


@patch("src.travels.trips_country_info._fetch_currency_rates", return_value={"EUR": 1.0, "CZK": 25.5})
@patch(
    "src.travels.trips_country_info._fetch_weather",
    return_value={
        "avg_temp_c": 15.0,
        "min_temp_c": 8.0,
        "max_temp_c": 22.0,
        "avg_precipitation_mm": 2.5,
        "rainy_days": 7,
    },
)
@patch("src.travels.trips_country_info._fetch_sunrise_sunset")
@patch("src.travels.trips_country_info._fetch_holidays_for_country")
def test_country_info_with_all_external_data(
    mock_holidays: MagicMock,
    mock_sunrise: MagicMock,
    _mock_weather: object,
    _mock_currency: object,
    admin_client: "TestClient",
    db_session: "Session",
) -> None:
    """Country info with mocked sunrise and holidays populated."""
    from src.models import TCCDestination, Trip, TripDestination, UNCountry
    from src.travels.models import CountryHoliday, SunriseSunset

    mock_sunrise.return_value = SunriseSunset(sunrise="06:30", sunset="18:30", day_length_hours=12.0)
    mock_holidays.return_value = [
        CountryHoliday(date="2026-03-05", name="Holiday", local_name="Svátek")
    ]

    country = UNCountry(
        name="Czechia",
        iso_alpha2="CZ",
        iso_alpha3="CZE",
        iso_numeric="203",
        continent="Europe",
        map_region_codes="203",
        currency_code="EUR",
        capital_lat=50.0,
        capital_lng=14.0,
        timezone="Europe/Prague",
        socket_types="C,E",
    )
    db_session.add(country)
    db_session.flush()

    tcc = TCCDestination(
        name="Prague", tcc_region="EUROPE", tcc_index=1, un_country_id=country.id
    )
    db_session.add(tcc)
    db_session.flush()

    trip = Trip(start_date=date(2026, 3, 1), end_date=date(2026, 3, 10))
    db_session.add(trip)
    db_session.flush()
    db_session.add(TripDestination(trip_id=trip.id, tcc_destination_id=tcc.id))
    db_session.commit()

    res = admin_client.get(f"/api/v1/travels/trips/{trip.id}/country-info")
    assert res.status_code == 200
    data = res.json()
    c = data["countries"][0]

    # Sunrise/sunset
    assert c["sunrise_sunset"] is not None
    assert c["sunrise_sunset"]["sunrise"] == "06:30"
    assert c["sunrise_sunset"]["sunset"] == "18:30"

    # Holidays
    assert len(c["holidays"]) == 1

    # Timezone offset
    assert c["timezone_offset_hours"] is not None
    assert c["timezone_offset_hours"] == 0.0  # CZ vs CZ
