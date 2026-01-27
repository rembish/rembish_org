from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class UserLastLocation(Base):
    """Stores the last known GPS location for each user."""

    __tablename__ = "user_last_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey("cities.id"), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="last_location")
    city: Mapped["City"] = relationship()

    def __repr__(self) -> str:
        return f"<UserLastLocation user={self.user_id} city={self.city_id}>"


# Import to complete relationship
from .travel import City  # noqa: E402, F401
from .user import User  # noqa: E402, F401
