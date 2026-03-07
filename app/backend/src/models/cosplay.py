from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class CosplayCostume(Base):
    """Cosplay costume with associated photos."""

    __tablename__ = "cosplay_costumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_photo_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cosplay_photos.id", ondelete="SET NULL", use_alter=True), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    photos: Mapped[list["CosplayPhoto"]] = relationship(
        back_populates="costume",
        cascade="all, delete-orphan",
        order_by="CosplayPhoto.sort_order",
        foreign_keys="[CosplayPhoto.costume_id]",
    )

    def __repr__(self) -> str:
        return f"<CosplayCostume #{self.id}: {self.name}>"


class CosplayPhoto(Base):
    """Individual cosplay photo belonging to a costume."""

    __tablename__ = "cosplay_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    costume_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cosplay_costumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    costume: Mapped[CosplayCostume] = relationship(
        back_populates="photos", foreign_keys=[costume_id]
    )

    def __repr__(self) -> str:
        return f"<CosplayPhoto #{self.id}: {self.filename}>"
