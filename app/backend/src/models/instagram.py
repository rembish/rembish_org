from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class InstagramPost(Base):
    """Instagram posts with labels for categorization."""

    __tablename__ = "instagram_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ig_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    permalink: Mapped[str] = mapped_column(String(255), nullable=False)

    # IG geotag data
    ig_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ig_location_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    ig_location_lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)

    # Labels
    un_country_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("un_countries.id"), nullable=True
    )
    tcc_destination_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tcc_destinations.id"), nullable=True
    )
    trip_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True
    )
    city_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cities.id", ondelete="SET NULL"), nullable=True
    )
    is_aerial: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Workflow
    labeled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    media: Mapped[list["InstagramMedia"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", order_by="InstagramMedia.media_order"
    )
    un_country: Mapped["UNCountry | None"] = relationship()
    tcc_destination: Mapped["TCCDestination | None"] = relationship()
    trip: Mapped["Trip | None"] = relationship()
    city: Mapped["City | None"] = relationship()

    def __repr__(self) -> str:
        return f"<InstagramPost #{self.id}: {self.ig_id}>"


class InstagramMedia(Base):
    """Individual media items within Instagram posts (images/videos)."""

    __tablename__ = "instagram_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("instagram_posts.id", ondelete="CASCADE"), nullable=False
    )
    ig_media_id: Mapped[str] = mapped_column(String(50), nullable=False)
    media_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    post: Mapped[InstagramPost] = relationship(back_populates="media")

    def __repr__(self) -> str:
        return f"<InstagramMedia #{self.id}: post={self.post_id} order={self.media_order}>"


# Import to complete relationships
from .travel import City, TCCDestination, Trip, UNCountry  # noqa: E402, F401
