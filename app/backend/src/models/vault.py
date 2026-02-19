from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class VaultDocument(Base):
    __tablename__ = "vault_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    doc_type: Mapped[str] = mapped_column(
        Enum("passport", "id_card", "drivers_license", name="doc_type_enum"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    proper_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    issuing_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    number_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    number_masked: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    notes_masked: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")

    user: Mapped["User"] = relationship(back_populates="vault_documents")

    def __repr__(self) -> str:
        return f"<VaultDocument #{self.id}: {self.label}>"


class VaultLoyaltyProgram(Base):
    __tablename__ = "vault_loyalty_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    program_name: Mapped[str] = mapped_column(String(100), nullable=False)
    alliance: Mapped[str] = mapped_column(
        Enum("star_alliance", "oneworld", "skyteam", "none", name="alliance_enum"),
        nullable=False,
        server_default="none",
    )
    tier: Mapped[str | None] = mapped_column(String(50), nullable=True)
    membership_number_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    membership_number_masked: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    notes_masked: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")

    user: Mapped["User"] = relationship(back_populates="vault_loyalty_programs")

    def __repr__(self) -> str:
        return f"<VaultLoyaltyProgram #{self.id}: {self.program_name}>"


class VaultVaccination(Base):
    __tablename__ = "vault_vaccinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    vaccine_name: Mapped[str] = mapped_column(String(100), nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dose_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_administered: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    batch_number_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    batch_number_masked: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    notes_masked: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship(back_populates="vault_vaccinations")

    def __repr__(self) -> str:
        return f"<VaultVaccination #{self.id}: {self.vaccine_name}>"


# Avoid circular imports
from .user import User  # noqa: E402, F401
