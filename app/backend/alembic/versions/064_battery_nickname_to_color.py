"""Replace batteries.nickname with batteries.color.

Color is a hex string (e.g. '#FF5733') for visual identification.
"""

import sqlalchemy as sa
from alembic import op

revision = "064"
down_revision = "063"


def upgrade() -> None:
    op.drop_column("batteries", "nickname")
    op.add_column("batteries", sa.Column("color", sa.String(7), nullable=True))


def downgrade() -> None:
    op.drop_column("batteries", "color")
    op.add_column("batteries", sa.Column("nickname", sa.String(100), nullable=True))
