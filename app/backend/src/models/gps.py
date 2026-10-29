from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

# stop/gap/foot/vehicle come from automatic processing; the rest only from analysis.
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
LEG_SOURCES = ("auto", "annotated")


class GpsTrack(Base):
    """One day of a GNSS logger track (one CSV file). Raw file lives in private storage."""

    __tablename__ = "gps_tracks"
    __table_args__ = (
        CheckConstraint("legs_source IN ('auto', 'annotated')", name="ck_gps_tracks_legs_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_file: Mapped[str] = mapped_column(String(200), nullable=False)
    # First point of the file, UTC. Logger file names (DDHHMMSS) repeat across months,
    # so this — not the name — identifies a track.
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, unique=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    raw_path: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_size: Mapped[int] = mapped_column(Integer, nullable=False)
    point_count: Mapped[int] = mapped_column(Integer, nullable=False)
    wake_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    poi_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    max_speed_kmh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    legs_source: Mapped[str] = mapped_column(String(10), nullable=False, default="auto")
    processing_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    trip: Mapped["Trip | None"] = relationship(back_populates="gps_tracks")
    legs: Mapped[list["GpsTrackLeg"]] = relationship(
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="GpsTrackLeg.seq",
    )

    def __repr__(self) -> str:
        return f"<GpsTrack #{self.id}: {self.local_date} {self.source_file}>"


class GpsTrackLeg(Base):
    """A stretch of one track day: a stop, a walk, a drive, a boat ride, or missing data."""

    __tablename__ = "gps_track_legs"
    __table_args__ = (
        UniqueConstraint("track_id", "seq", name="uq_gps_track_legs_track_seq"),
        CheckConstraint(
            "mode IN (" + ", ".join(f"'{m}'" for m in LEG_MODES) + ")",
            name="ck_gps_track_legs_mode",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gps_tracks.id", ondelete="CASCADE"), nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    max_speed_kmh: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    # Representative position (centroid for stops) — used for stop markers.
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    # Simplified polylines, [[[lat, lon], ...], ...] — split wherever the logger paused.
    lines: Mapped[list[list[list[float]]]] = mapped_column(JSON, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    track: Mapped[GpsTrack] = relationship(back_populates="legs")

    def __repr__(self) -> str:
        return f"<GpsTrackLeg #{self.id}: {self.mode} {self.started_at}>"


# Imported at module level to complete relationship references
from .travel import Trip  # noqa: E402, F401
