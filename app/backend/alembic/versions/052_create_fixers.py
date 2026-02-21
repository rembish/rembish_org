"""Create fixers and fixer_countries tables

Revision ID: 052
Revises: 051
Create Date: 2026-02-21

Contact book for travel fixers: guides, drivers, coordinators, agencies.
"""

import sqlalchemy as sa
from alembic import op

revision = "052"
down_revision = "051"


def upgrade() -> None:
    op.create_table(
        "fixers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "name",
            sa.String(200),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum(
                "guide",
                "fixer",
                "driver",
                "coordinator",
                "agency",
                name="fixer_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("whatsapp", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("rating", sa.Integer, nullable=True),
        sa.Column("links", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.CheckConstraint("rating >= 1 AND rating <= 4", name="chk_fixer_rating"),
    )

    op.create_table(
        "fixer_countries",
        sa.Column(
            "fixer_id",
            sa.Integer,
            sa.ForeignKey("fixers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("country_code", sa.String(2), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("fixer_countries")
    op.drop_table("fixers")
