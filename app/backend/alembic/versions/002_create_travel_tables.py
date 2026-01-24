"""Create travel tables (un_countries, tcc_destinations, visits)

Revision ID: 002
Revises: 001
Create Date: 2026-01-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "un_countries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("iso_alpha2", sa.String(2), nullable=False),
        sa.Column("iso_alpha3", sa.String(3), nullable=False),
        sa.Column("iso_numeric", sa.String(10), nullable=False),
        sa.Column("map_region_codes", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("iso_alpha2"),
        sa.UniqueConstraint("iso_alpha3"),
        sa.UniqueConstraint("iso_numeric"),
    )

    op.create_table(
        "tcc_destinations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tcc_region", sa.String(100), nullable=False),
        sa.Column("tcc_index", sa.Integer(), nullable=False),
        sa.Column("un_country_id", sa.Integer(), nullable=True),
        sa.Column("map_region_code", sa.String(10), nullable=True),
        sa.ForeignKeyConstraint(["un_country_id"], ["un_countries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tcc_index"),
    )

    op.create_table(
        "visits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tcc_destination_id", sa.Integer(), nullable=False),
        sa.Column("first_visit_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tcc_destination_id"], ["tcc_destinations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tcc_destination_id"),
    )


def downgrade() -> None:
    op.drop_table("visits")
    op.drop_table("tcc_destinations")
    op.drop_table("un_countries")
