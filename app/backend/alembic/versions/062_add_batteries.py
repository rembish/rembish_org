"""Add batteries table.

Track drone batteries as first-class entities with serial numbers,
capacity specs, and lifecycle dates.
"""

import sqlalchemy as sa
from alembic import op

revision = "062"
down_revision = "061"


def upgrade() -> None:
    op.create_table(
        "batteries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("drone_id", sa.Integer, sa.ForeignKey("drones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("serial_number", sa.String(100), nullable=False, unique=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("nickname", sa.String(100), nullable=True),
        sa.Column("design_capacity_mah", sa.Integer, nullable=True),
        sa.Column("cell_count", sa.Integer, nullable=True),
        sa.Column("acquired_date", sa.Date, nullable=True),
        sa.Column("retired_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_batteries_drone_id", "batteries", ["drone_id"])


def downgrade() -> None:
    op.drop_index("ix_batteries_drone_id", table_name="batteries")
    op.drop_table("batteries")
