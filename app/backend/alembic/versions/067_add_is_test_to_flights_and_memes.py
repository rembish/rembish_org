"""Add is_test column to drone_flights and memes for iOS app testing."""

import sqlalchemy as sa
from alembic import op

revision = "067"
down_revision = "066"


def upgrade() -> None:
    op.add_column(
        "drone_flights",
        sa.Column("is_test", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "memes",
        sa.Column("is_test", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("memes", "is_test")
    op.drop_column("drone_flights", "is_test")
