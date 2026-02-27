from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Meme(Base):
    """Meme image for feed curation."""

    __tablename__ = "memes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="telegram")
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_site_worthy: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    telegram_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Meme #{self.id}: {self.status} ({self.category})>"
