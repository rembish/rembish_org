from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class TripType(StrEnum):
    """Trip type enumeration."""

    regular = "regular"
    work = "work"
    relocation = "relocation"


class UNCountry(Base):
    """UN member states (193 countries) with map region codes."""

    __tablename__ = "un_countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    iso_alpha2: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    iso_alpha3: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    iso_numeric: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    continent: Mapped[str] = mapped_column(String(50), nullable=False, default="Unknown")
    # Map region codes - some territories have separate polygons
    map_region_codes: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Comma-separated codes for territories

    # Activity tracking: driving_type = 'rental', 'own', or NULL
    driving_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    drone_flown: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Reference data
    socket_types: Mapped[str | None] = mapped_column(String(50), nullable=True)
    voltage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    driving_side: Mapped[str | None] = mapped_column(String(5), nullable=True)
    emergency_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tap_water: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    capital_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    capital_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Extended reference data
    languages: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipping: Mapped[str | None] = mapped_column(String(200), nullable=True)
    speed_limits: Mapped[str | None] = mapped_column(String(50), nullable=True)
    visa_free_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eu_roaming: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    tcc_destinations: Mapped[list["TCCDestination"]] = relationship(back_populates="un_country")

    def __repr__(self) -> str:
        return f"<UNCountry #{self.id}: {self.name}>"


class TCCDestination(Base):
    """TCC destinations (330 total) - includes territories and sub-regions."""

    __tablename__ = "tcc_destinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tcc_region: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "EUROPE & MEDITERRANEAN"
    tcc_index: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True
    )  # TCC's numbering 1-330

    # Link to UN country (nullable for non-UN territories like Kosovo)
    un_country_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("un_countries.id"), nullable=True
    )
    un_country: Mapped[UNCountry | None] = relationship(back_populates="tcc_destinations")

    # For territories with their own map polygon (e.g., Somaliland, Kosovo)
    map_region_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # ISO code override (Kosovo=XK, Vatican=VA, England=gb-eng, etc.)
    iso_alpha2: Mapped[str | None] = mapped_column(String(10), nullable=True)

    visit: Mapped["Visit | None"] = relationship(back_populates="tcc_destination")
    trip_destinations: Mapped[list["TripDestination"]] = relationship(
        back_populates="tcc_destination"
    )

    def __repr__(self) -> str:
        return f"<TCCDestination #{self.id}: {self.name}>"


class Visit(Base):
    """Records of first visits to TCC destinations."""

    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tcc_destination_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tcc_destinations.id"), nullable=False, unique=True
    )
    tcc_destination: Mapped[TCCDestination] = relationship(back_populates="visit")

    first_visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        name = self.tcc_destination.name if self.tcc_destination else "Unknown"
        return f"<Visit #{self.id}: {name}>"


class Microstate(Base):
    """Small countries/territories that need map markers to be visible."""

    __tablename__ = "microstates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    map_region_code: Mapped[str] = mapped_column(String(10), nullable=False)

    def __repr__(self) -> str:
        return f"<Microstate #{self.id}: {self.name}>"


class NMRegion(Base):
    """NomadMania regions (1301 total)."""

    __tablename__ = "nm_regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)  # Country/territory prefix
    visited: Mapped[bool] = mapped_column(default=False)
    first_visited_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_visited_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<NMRegion #{self.id}: {self.name}>"


class Trip(Base):
    """Personal trips with dates and metadata."""

    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Companions (normalized text, e.g., "Аня, Лёша, +2") - legacy, will be removed
    companions: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Count of unnamed/other participants
    other_participants_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Trip metadata
    trip_type: Mapped[str] = mapped_column(String(20), default="regular")
    flights_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    working_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rental_car: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Original data from spreadsheet (for reference)
    raw_countries: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_cities: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Departure/arrival type for vacation day calculation
    departure_type: Mapped[str] = mapped_column(String(10), default="morning")
    arrival_type: Mapped[str] = mapped_column(String(10), default="evening")

    # Hide from photos page (for trips with few/unimportant photos)
    hidden_from_photos: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationships
    destinations: Mapped[list["TripDestination"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )
    participants: Mapped[list["TripParticipant"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )
    cities: Mapped[list["TripCity"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", order_by="TripCity.order"
    )
    flights: Mapped[list["Flight"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Trip #{self.id}: {self.start_date}>"


class TripDestination(Base):
    """Junction table linking trips to TCC destinations."""

    __tablename__ = "trip_destinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    tcc_destination_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tcc_destinations.id"), nullable=False
    )

    # Was this a partial visit (from parentheses in spreadsheet)?
    is_partial: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    trip: Mapped[Trip] = relationship(back_populates="destinations")
    tcc_destination: Mapped[TCCDestination] = relationship(back_populates="trip_destinations")

    def __repr__(self) -> str:
        return f"<TripDestination trip={self.trip_id} tcc={self.tcc_destination_id}>"


class TripParticipant(Base):
    """Junction table linking trips to user participants."""

    __tablename__ = "trip_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    trip: Mapped[Trip] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="trip_participations")

    def __repr__(self) -> str:
        return f"<TripParticipant trip={self.trip_id} user={self.user_id}>"


class City(Base):
    """Geocoded cities reference table."""

    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)  # ISO alpha-2
    display_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lat: Mapped[float | None] = mapped_column(nullable=True)
    lng: Mapped[float | None] = mapped_column(nullable=True)
    geocoded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    trip_cities: Mapped[list["TripCity"]] = relationship(back_populates="city")

    def __repr__(self) -> str:
        return f"<City #{self.id}: {self.name}, {self.country}>"


class TripCity(Base):
    """Cities visited during a trip."""

    __tablename__ = "trip_cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_partial: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    city_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cities.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    trip: Mapped[Trip] = relationship(back_populates="cities")
    city: Mapped[City | None] = relationship(back_populates="trip_cities")

    def __repr__(self) -> str:
        return f"<TripCity trip={self.trip_id} name={self.name}>"


class Airport(Base):
    """Airport reference data, upserted from AeroDataBox API responses."""

    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iata_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<Airport #{self.id}: {self.iata_code}>"


class Flight(Base):
    """Individual flight record linked to a trip."""

    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flight_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    flight_number: Mapped[str] = mapped_column(String(10), nullable=False)
    airline_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    departure_airport_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("airports.id"), nullable=False
    )
    arrival_airport_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("airports.id"), nullable=False
    )
    departure_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    arrival_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    arrival_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    terminal: Mapped[str | None] = mapped_column(String(10), nullable=True)
    arrival_terminal: Mapped[str | None] = mapped_column(String(10), nullable=True)
    gate: Mapped[str | None] = mapped_column(String(10), nullable=True)
    aircraft_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    seat: Mapped[str | None] = mapped_column(String(10), nullable=True)
    booking_reference: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    trip: Mapped[Trip] = relationship(back_populates="flights")
    departure_airport: Mapped[Airport] = relationship(foreign_keys=[departure_airport_id])
    arrival_airport: Mapped[Airport] = relationship(foreign_keys=[arrival_airport_id])

    def __repr__(self) -> str:
        return f"<Flight #{self.id}: {self.flight_number} on {self.flight_date}>"


# Import to complete relationship
from .user import User  # noqa: E402, F401
