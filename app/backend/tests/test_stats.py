"""Tests for aircraft type family grouping and stats helpers."""

from src.travels.stats import _aircraft_family


def test_airbus_a320_family() -> None:
    assert _aircraft_family("Airbus A320") == "Airbus A320 family"
    assert _aircraft_family("Airbus A321neo") == "Airbus A320 family"
    assert _aircraft_family("Airbus A319") == "Airbus A320 family"
    assert _aircraft_family("Airbus A318") == "Airbus A320 family"


def test_airbus_widebody() -> None:
    assert _aircraft_family("Airbus A330-300") == "Airbus A330"
    assert _aircraft_family("Airbus A340-600") == "Airbus A340"
    assert _aircraft_family("Airbus A350-900") == "Airbus A350"
    assert _aircraft_family("Airbus A380-800") == "Airbus A380"


def test_boeing() -> None:
    assert _aircraft_family("Boeing 737-800") == "Boeing 737"
    assert _aircraft_family("Boeing 777-300ER") == "Boeing 777"
    assert _aircraft_family("Boeing 787-9") == "Boeing 787"


def test_atr() -> None:
    assert _aircraft_family("ATR 72") == "ATR 72"
    assert _aircraft_family("ATR42-600") == "ATR 42"
    assert _aircraft_family("ATR") == "ATR"


def test_embraer() -> None:
    assert _aircraft_family("Embraer 190") == "Embraer E-Jet"
    assert _aircraft_family("Embraer 175") == "Embraer E-Jet"
    assert _aircraft_family("ERJ-145") == "Embraer 145"
    assert _aircraft_family("Embraer") == "Embraer"


def test_bombardier_crj() -> None:
    assert _aircraft_family("CRJ-900") == "Bombardier CRJ"
    assert _aircraft_family("Canadair Regional Jet") == "Bombardier CRJ"


def test_dash() -> None:
    assert _aircraft_family("Dash 8-400") == "De Havilland Dash"
    assert _aircraft_family("DHC-8") == "De Havilland Dash"
    assert _aircraft_family("De Havilland Canada Dash 8") == "De Havilland Dash"


def test_fallback() -> None:
    assert _aircraft_family("Cessna 172") == "Cessna 172"
    assert _aircraft_family("Saab 340") == "Saab 340"
