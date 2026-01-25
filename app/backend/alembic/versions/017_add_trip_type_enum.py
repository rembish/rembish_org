"""Replace is_work_trip boolean with trip_type enum.

Revision ID: 017
Revises: 016
Create Date: 2025-01-25
"""

from alembic import op
import sqlalchemy as sa

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add trip_type column (regular, work, relocation)
    op.add_column(
        "trips",
        sa.Column(
            "trip_type",
            sa.String(20),
            nullable=False,
            server_default="regular",
        ),
    )

    # Migrate existing is_work_trip data (if any trips exist)
    op.execute("UPDATE trips SET trip_type = 'work' WHERE is_work_trip = 1")

    # Drop old boolean column
    op.drop_column("trips", "is_work_trip")

    # NOTE: Relocation trip (Sep 2008 Prague move) should be added via import script
    # or manually: INSERT INTO trips (start_date, trip_type) VALUES ('2008-09-20', 'relocation')


def downgrade() -> None:
    # Re-add is_work_trip column
    op.add_column(
        "trips",
        sa.Column("is_work_trip", sa.Boolean(), nullable=False, server_default="0"),
    )

    # Migrate back
    op.execute("UPDATE trips SET is_work_trip = 1 WHERE trip_type = 'work'")

    # Drop trip_type
    op.drop_column("trips", "trip_type")
