from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


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

    tcc_destinations: Mapped[list["TCCDestination"]] = relationship(
        back_populates="un_country"
    )

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

    visit: Mapped["Visit | None"] = relationship(back_populates="tcc_destination")

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
        return f"<Visit #{self.id}: {self.tcc_destination.name if self.tcc_destination else 'Unknown'}>"


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
