"""Create drones table

Revision ID: 058
Revises: 057
Create Date: 2026-02-23

Stores drone hardware registry (name, model, serial, dates).
"""

import sqlalchemy as sa
from alembic import op

revision = "058"
down_revision = "057"


def upgrade() -> None:
    op.create_table(
        "drones",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("acquired_date", sa.Date, nullable=True),
        sa.Column("retired_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("drones")
