from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

_now = lambda: datetime.now(UTC)  # noqa: E731


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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now, onupdate=_now
    )

    user: Mapped["User"] = relationship(back_populates="vault_documents")
    files: Mapped[list["VaultFile"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now, onupdate=_now
    )

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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now, onupdate=_now
    )

    user: Mapped["User"] = relationship(back_populates="vault_vaccinations")
    files: Mapped[list["VaultFile"]] = relationship(
        back_populates="vaccination", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VaultVaccination #{self.id}: {self.vaccine_name}>"


class VaultTravelDoc(Base):
    __tablename__ = "vault_travel_docs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    doc_type: Mapped[str] = mapped_column(
        Enum(
            "e_visa",
            "eta",
            "esta",
            "etias",
            "loi",
            "entry_permit",
            "travel_insurance",
            "vaccination_cert",
            "other",
            name="travel_doc_type_enum",
        ),
        nullable=False,
    )
    document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("vault_documents.id", ondelete="SET NULL"), nullable=True
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    entry_type: Mapped[str | None] = mapped_column(
        Enum("single", "double", "multiple", name="entry_type_enum"),
        nullable=True,
    )
    notes_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    notes_masked: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now, onupdate=_now
    )

    user: Mapped["User"] = relationship(back_populates="vault_travel_docs")
    passport: Mapped["VaultDocument | None"] = relationship(foreign_keys=[document_id])
    files: Mapped[list["VaultFile"]] = relationship(
        back_populates="travel_doc", cascade="all, delete-orphan"
    )
    trips: Mapped[list["TripTravelDoc"]] = relationship(
        back_populates="travel_doc", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VaultTravelDoc #{self.id}: {self.label}>"


class VaultFile(Base):
    __tablename__ = "vault_files"
    __table_args__ = (
        CheckConstraint(
            "document_id IS NOT NULL OR vaccination_id IS NOT NULL OR travel_doc_id IS NOT NULL",
            name="chk_vault_files_parent",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("vault_documents.id", ondelete="CASCADE"), nullable=True
    )
    vaccination_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("vault_vaccinations.id", ondelete="CASCADE"), nullable=True
    )
    travel_doc_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("vault_travel_docs.id", ondelete="CASCADE"), nullable=True
    )
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    document: Mapped[VaultDocument | None] = relationship(back_populates="files")
    vaccination: Mapped[VaultVaccination | None] = relationship(back_populates="files")
    travel_doc: Mapped[VaultTravelDoc | None] = relationship(back_populates="files")

    def __repr__(self) -> str:
        return f"<VaultFile #{self.id}: {self.file_path}>"


class TripTravelDoc(Base):
    __tablename__ = "trip_travel_docs"
    __table_args__ = (UniqueConstraint("trip_id", "travel_doc_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    travel_doc_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vault_travel_docs.id", ondelete="CASCADE"), index=True
    )

    trip: Mapped["Trip"] = relationship(back_populates="travel_docs")
    travel_doc: Mapped[VaultTravelDoc] = relationship(back_populates="trips")

    def __repr__(self) -> str:
        return f"<TripTravelDoc trip={self.trip_id} doc={self.travel_doc_id}>"


class TripPassport(Base):
    __tablename__ = "trip_passports"
    __table_args__ = (UniqueConstraint("trip_id", "document_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vault_documents.id", ondelete="CASCADE")
    )

    trip: Mapped["Trip"] = relationship(back_populates="passports")
    document: Mapped[VaultDocument] = relationship()

    def __repr__(self) -> str:
        return f"<TripPassport trip={self.trip_id} doc={self.document_id}>"


# Avoid circular imports
from .travel import Trip  # noqa: E402, F401
from .user import User  # noqa: E402, F401
