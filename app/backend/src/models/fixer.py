from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

_now = lambda: datetime.now(UTC)  # noqa: E731


class Fixer(Base):
    __tablename__ = "fixers"
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 4", name="chk_fixer_rating"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("guide", "fixer", "driver", "coordinator", "agency", name="fixer_type_enum"),
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    links: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now, onupdate=_now
    )

    countries: Mapped[list["FixerCountry"]] = relationship(
        back_populates="fixer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Fixer #{self.id}: {self.name}>"


class FixerCountry(Base):
    __tablename__ = "fixer_countries"

    fixer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fixers.id", ondelete="CASCADE"), primary_key=True
    )
    country_code: Mapped[str] = mapped_column(String(2), primary_key=True)

    fixer: Mapped[Fixer] = relationship(back_populates="countries")

    def __repr__(self) -> str:
        return f"<FixerCountry fixer={self.fixer_id} country={self.country_code}>"
