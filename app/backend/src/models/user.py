from datetime import date

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    picture: Mapped[str | None] = mapped_column(String(512), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    trip_participations: Mapped[list["TripParticipant"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    last_location: Mapped["UserLastLocation | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    vault_documents: Mapped[list["VaultDocument"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    vault_loyalty_programs: Mapped[list["VaultLoyaltyProgram"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    vault_vaccinations: Mapped[list["VaultVaccination"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    vault_travel_docs: Mapped[list["VaultTravelDoc"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User #{self.id}: {self.email}>"


# Import here to avoid circular imports
from .location import UserLastLocation  # noqa: E402, F401
from .travel import TripParticipant  # noqa: E402, F401
from .vault import (  # noqa: E402, F401
    VaultDocument,
    VaultLoyaltyProgram,
    VaultTravelDoc,
    VaultVaccination,
)
