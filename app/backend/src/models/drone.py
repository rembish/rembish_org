from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Drone(Base):
    """Drone hardware registry."""

    __tablename__ = "drones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acquired_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    retired_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    flights: Mapped[list["DroneFlight"]] = relationship(back_populates="drone")

    def __repr__(self) -> str:
        return f"<Drone #{self.id}: {self.name} ({self.model})>"


class DroneFlight(Base):
    """Individual drone flight record from DJI Fly app."""

    __tablename__ = "drone_flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    drone_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("drones.id"), nullable=True, index=True
    )
    trip_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True
    )
    flight_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    takeoff_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_speed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    photos: Mapped[int] = mapped_column(Integer, default=0)
    video_sec: Mapped[int] = mapped_column(Integer, default=0)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    city: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    source_file: Mapped[str | None] = mapped_column(String(200), nullable=True)
    flight_path: Mapped[list[list[float]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    drone: Mapped[Drone | None] = relationship(back_populates="flights")
    trip: Mapped["Trip | None"] = relationship(back_populates="drone_flights")

    def __repr__(self) -> str:
        return f"<DroneFlight #{self.id}: {self.flight_date}>"


# Imported at module level to complete relationship references
from .travel import Trip  # noqa: E402, F401
