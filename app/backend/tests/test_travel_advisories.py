"""Tests for travel advisories computation."""

from datetime import date

from fastapi.testclient import TestClient

from src.travels.travel_advisories import (
    _carnival_dates,
    _easter_date,
    _eid_al_adha_dates,
    _eid_al_fitr_dates,
    _oktoberfest_dates,
    _overlaps,
    _ramadan_dates,
    get_travel_advisories,
)


# ---------------------------------------------------------------------------
# Date computation tests
# ---------------------------------------------------------------------------


class TestEasterDate:
    def test_known_years(self) -> None:
        assert _easter_date(2024) == date(2024, 3, 31)
        assert _easter_date(2025) == date(2025, 4, 20)
        assert _easter_date(2026) == date(2026, 4, 5)
        assert _easter_date(2027) == date(2027, 3, 28)

    def test_easter_is_sunday(self) -> None:
        for year in range(2024, 2031):
            d = _easter_date(year)
            assert d.weekday() == 6, f"Easter {year} is not Sunday"


class TestRamadanDates:
    def test_returns_dates_for_known_year(self) -> None:
        dates = _ramadan_dates(2026)
        assert dates is not None
        start, end = dates
        assert start.year == 2026 or end.year == 2026
        assert start < end
        # Ramadan 2026 starts around Feb 18
        assert start.month in (2, 3)

    def test_ramadan_lasts_29_or_30_days(self) -> None:
        for year in range(2024, 2030):
            dates = _ramadan_dates(year)
            assert dates is not None
            duration = (dates[1] - dates[0]).days + 1
            assert duration in (29, 30), f"Ramadan {year} is {duration} days"


class TestEidDates:
    def test_eid_al_fitr_after_ramadan(self) -> None:
        for year in range(2024, 2030):
            ramadan = _ramadan_dates(year)
            fitr = _eid_al_fitr_dates(year)
            if ramadan and fitr:
                # Eid al-Fitr starts day after Ramadan ends
                assert fitr[0] == ramadan[1] + __import__("datetime").timedelta(days=1)

    def test_eid_al_fitr_lasts_3_days(self) -> None:
        for year in range(2024, 2030):
            dates = _eid_al_fitr_dates(year)
            assert dates is not None
            assert (dates[1] - dates[0]).days == 2

    def test_eid_al_adha_lasts_4_days(self) -> None:
        for year in range(2024, 2030):
            dates = _eid_al_adha_dates(year)
            assert dates is not None
            assert (dates[1] - dates[0]).days == 3


class TestCarnivalDates:
    def test_carnival_before_easter(self) -> None:
        for year in range(2024, 2031):
            start, end = _carnival_dates(year)
            easter = _easter_date(year)
            # Shrove Tuesday is 47 days before Easter
            assert end == easter - __import__("datetime").timedelta(days=47)
            # Start is Saturday before Shrove Tuesday
            assert start.weekday() == 5  # Saturday
            assert end.weekday() == 1  # Tuesday


class TestOktoberfestDates:
    def test_ends_on_sunday(self) -> None:
        for year in range(2024, 2031):
            start, end = _oktoberfest_dates(year)
            assert start == date(year, 9, 16)
            assert end.weekday() == 6  # Sunday
            assert end.month == 10

    def test_oct1_is_sunday(self) -> None:
        # 2028-10-01 is a Sunday — should end on Oct 1, not Oct 8
        start, end = _oktoberfest_dates(2028)
        assert end == date(2028, 10, 1)


# ---------------------------------------------------------------------------
# Overlap logic
# ---------------------------------------------------------------------------


class TestOverlap:
    def test_no_overlap(self) -> None:
        assert not _overlaps(date(2026, 3, 1), date(2026, 3, 10), date(2026, 4, 1), date(2026, 4, 5))

    def test_full_overlap(self) -> None:
        assert _overlaps(date(2026, 3, 1), date(2026, 3, 10), date(2026, 3, 1), date(2026, 3, 10))

    def test_partial_overlap(self) -> None:
        assert _overlaps(date(2026, 3, 1), date(2026, 3, 10), date(2026, 3, 8), date(2026, 3, 15))

    def test_event_inside_trip(self) -> None:
        assert _overlaps(date(2026, 3, 5), date(2026, 3, 5), date(2026, 3, 1), date(2026, 3, 10))

    def test_single_day_boundary(self) -> None:
        assert _overlaps(date(2026, 3, 10), date(2026, 3, 15), date(2026, 3, 1), date(2026, 3, 10))
        assert not _overlaps(
            date(2026, 3, 11), date(2026, 3, 15), date(2026, 3, 1), date(2026, 3, 10)
        )


# ---------------------------------------------------------------------------
# Country matching
# ---------------------------------------------------------------------------


class TestCountryMatching:
    def test_ramadan_for_saudi_arabia(self) -> None:
        advisories = get_travel_advisories("SA", date(2026, 2, 1), date(2026, 3, 31))
        ramadan = [a for a in advisories if a.event_name == "Ramadan"]
        assert len(ramadan) == 1
        assert ramadan[0].severity == "high"
        assert ramadan[0].category == "restriction"

    def test_no_ramadan_for_france(self) -> None:
        advisories = get_travel_advisories("FR", date(2026, 2, 1), date(2026, 3, 31))
        ramadan = [a for a in advisories if a.event_name == "Ramadan"]
        assert len(ramadan) == 0

    def test_ramadan_tier2_for_egypt(self) -> None:
        advisories = get_travel_advisories("EG", date(2026, 2, 1), date(2026, 3, 31))
        ramadan = [a for a in advisories if a.event_name == "Ramadan"]
        assert len(ramadan) == 1
        assert ramadan[0].severity == "medium"

    def test_ramadan_tier3_for_turkey(self) -> None:
        advisories = get_travel_advisories("TR", date(2026, 2, 1), date(2026, 3, 31))
        ramadan = [a for a in advisories if a.event_name == "Ramadan"]
        assert len(ramadan) == 1
        assert ramadan[0].severity == "low"

    def test_nyepi_for_indonesia(self) -> None:
        advisories = get_travel_advisories("ID", date(2026, 3, 1), date(2026, 3, 31))
        nyepi = [a for a in advisories if "Nyepi" in a.event_name]
        assert len(nyepi) == 1
        assert nyepi[0].severity == "high"

    def test_no_nyepi_for_malaysia(self) -> None:
        advisories = get_travel_advisories("MY", date(2026, 3, 1), date(2026, 3, 31))
        nyepi = [a for a in advisories if "Nyepi" in a.event_name]
        assert len(nyepi) == 0

    def test_songkran_for_thailand(self) -> None:
        advisories = get_travel_advisories("TH", date(2026, 4, 10), date(2026, 4, 20))
        songkran = [a for a in advisories if "Songkran" in a.event_name]
        assert len(songkran) == 1

    def test_holi_for_india(self) -> None:
        advisories = get_travel_advisories("IN", date(2026, 3, 1), date(2026, 3, 5))
        holi = [a for a in advisories if "Holi" in a.event_name]
        assert len(holi) == 1

    def test_chinese_new_year_for_china(self) -> None:
        advisories = get_travel_advisories("CN", date(2026, 2, 15), date(2026, 2, 25))
        cny = [a for a in advisories if a.event_name == "Chinese New Year"]
        assert len(cny) == 1

    def test_diwali_for_india(self) -> None:
        advisories = get_travel_advisories("IN", date(2026, 11, 1), date(2026, 11, 15))
        diwali = [a for a in advisories if "Diwali" in a.event_name]
        assert len(diwali) == 1


# ---------------------------------------------------------------------------
# No advisories outside date range
# ---------------------------------------------------------------------------


class TestNoOverlap:
    def test_no_advisories_outside_range(self) -> None:
        # Trip in August — no Ramadan, Carnival, CNY, etc. for Germany
        advisories = get_travel_advisories("DE", date(2026, 8, 1), date(2026, 8, 15))
        assert len(advisories) == 0

    def test_empty_country_code(self) -> None:
        assert get_travel_advisories("", date(2026, 1, 1), date(2026, 12, 31)) == []


# ---------------------------------------------------------------------------
# Sorting: restrictions before events
# ---------------------------------------------------------------------------


class TestSorting:
    def test_restrictions_before_events(self) -> None:
        # Indonesia in March 2026: has Ramadan (restriction) + Nyepi (restriction)
        advisories = get_travel_advisories("ID", date(2026, 2, 1), date(2026, 4, 30))
        categories = [a.category for a in advisories]
        # All restrictions should come before events
        restriction_indices = [i for i, c in enumerate(categories) if c == "restriction"]
        event_indices = [i for i, c in enumerate(categories) if c == "event"]
        if restriction_indices and event_indices:
            assert max(restriction_indices) < min(event_indices)


# ---------------------------------------------------------------------------
# Sporting events
# ---------------------------------------------------------------------------


class TestSportingEvents:
    def test_winter_olympics_2026_italy(self) -> None:
        advisories = get_travel_advisories("IT", date(2026, 2, 1), date(2026, 2, 28))
        olympics = [a for a in advisories if "Olympics" in a.event_name]
        assert len(olympics) == 1
        assert olympics[0].severity == "medium"

    def test_no_olympics_for_spain_2026(self) -> None:
        advisories = get_travel_advisories("ES", date(2026, 2, 1), date(2026, 2, 28))
        olympics = [a for a in advisories if "Olympics" in a.event_name]
        assert len(olympics) == 0

    def test_fifa_2026_for_us(self) -> None:
        advisories = get_travel_advisories("US", date(2026, 6, 1), date(2026, 7, 31))
        fifa = [a for a in advisories if "FIFA" in a.event_name]
        assert len(fifa) == 1
        assert fifa[0].severity == "medium"

    def test_fifa_2026_for_mexico(self) -> None:
        advisories = get_travel_advisories("MX", date(2026, 6, 1), date(2026, 7, 31))
        fifa = [a for a in advisories if "FIFA" in a.event_name]
        assert len(fifa) == 1


# ---------------------------------------------------------------------------
# Cross-year trips
# ---------------------------------------------------------------------------


class TestCrossYear:
    def test_cross_year_trip(self) -> None:
        # Dec 2025 - Jan 2026 trip to China should check CNY 2026
        advisories = get_travel_advisories("CN", date(2025, 12, 15), date(2026, 2, 28))
        cny = [a for a in advisories if a.event_name == "Chinese New Year"]
        # Should find CNY for 2025 or 2026
        assert len(cny) >= 1

    def test_three_year_trip_includes_middle_year(self) -> None:
        # Trip spanning 2025–2027 for Thailand: should find Songkran 2026 (middle year)
        advisories = get_travel_advisories("TH", date(2025, 7, 1), date(2027, 2, 28))
        songkran = [a for a in advisories if "Songkran" in a.event_name]
        assert len(songkran) >= 1
        # Specifically check that 2026 Songkran is included
        songkran_2026 = [a for a in songkran if "2026-04" in a.start_date]
        assert len(songkran_2026) == 1


# ---------------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------------


class TestDedup:
    def test_no_duplicate_events(self) -> None:
        # Even for cross-year query, same event should not appear twice
        advisories = get_travel_advisories("TH", date(2026, 4, 1), date(2026, 4, 30))
        songkran = [a for a in advisories if "Songkran" in a.event_name]
        assert len(songkran) == 1

    def test_no_duplicate_ramadan(self) -> None:
        advisories = get_travel_advisories("SA", date(2026, 1, 1), date(2026, 12, 31))
        ramadan = [a for a in advisories if a.event_name == "Ramadan"]
        assert len(ramadan) == 1


# ---------------------------------------------------------------------------
# Thai alcohol bans
# ---------------------------------------------------------------------------


class TestThaiAlcoholBans:
    def test_multiple_ban_days(self) -> None:
        # Full year 2026 should have 5 ban days
        advisories = get_travel_advisories("TH", date(2026, 1, 1), date(2026, 12, 31))
        bans = [a for a in advisories if "Alcohol Ban" in a.event_name]
        assert len(bans) == 5

    def test_single_ban_day(self) -> None:
        # March 2026 has one ban day (Mar 3)
        advisories = get_travel_advisories("TH", date(2026, 3, 1), date(2026, 3, 5))
        bans = [a for a in advisories if "Alcohol Ban" in a.event_name]
        assert len(bans) == 1


# ---------------------------------------------------------------------------
# API-level tests for /api/v1/travels/advisories/{country_code}
# ---------------------------------------------------------------------------


class TestAdvisoriesEndpoint:
    def test_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/api/v1/travels/advisories/SA?start_date=2026-02-01&end_date=2026-03-31")
        assert resp.status_code == 401

    def test_returns_advisories(self, admin_client: TestClient) -> None:
        resp = admin_client.get(
            "/api/v1/travels/advisories/SA?start_date=2026-02-01&end_date=2026-03-31"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "advisories" in data
        ramadan = [a for a in data["advisories"] if a["event_name"] == "Ramadan"]
        assert len(ramadan) == 1
        assert ramadan[0]["severity"] == "high"
        assert ramadan[0]["category"] == "restriction"

    def test_invalid_date_format(self, admin_client: TestClient) -> None:
        resp = admin_client.get(
            "/api/v1/travels/advisories/SA?start_date=not-a-date&end_date=2026-03-31"
        )
        assert resp.status_code == 400

    def test_missing_query_params(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/api/v1/travels/advisories/SA")
        assert resp.status_code == 422

    def test_empty_result_for_unaffected_country(self, admin_client: TestClient) -> None:
        resp = admin_client.get(
            "/api/v1/travels/advisories/IS?start_date=2026-08-01&end_date=2026-08-15"
        )
        assert resp.status_code == 200
        assert resp.json()["advisories"] == []

    def test_country_code_case_insensitive(self, admin_client: TestClient) -> None:
        resp = admin_client.get(
            "/api/v1/travels/advisories/th?start_date=2026-04-10&end_date=2026-04-20"
        )
        assert resp.status_code == 200
        songkran = [a for a in resp.json()["advisories"] if "Songkran" in a["event_name"]]
        assert len(songkran) == 1
