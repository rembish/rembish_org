"""Add per-territory country-info overrides to tcc_destinations.

Migration 070 linked dependent territories to their sovereign so the trip Info tab
had something to show. That inherits everything, which is wrong for a surprising
number of them: the U.S. Virgin Islands drive on the left while the US drives
right, the UK's Caribbean territories run 110-120V on Type A/B rather than 230V
Type G, and every territory with its own timezone was being given its sovereign's
capital for weather, sunrise and local time.

These columns hold only the values that differ from the sovereign; NULL means
"inherit". Seeded in 072.

lat/lng are deliberately not called capital_lat/capital_lng as on un_countries —
Torshavn is not a capital in that sense. They are the point used for weather and
sunrise lookups.
"""

import sqlalchemy as sa

from alembic import op

revision = "071"
down_revision = "070"

COLUMNS = (
    ("socket_types", sa.String(50)),
    ("voltage", sa.String(20)),
    ("driving_side", sa.String(5)),
    ("tap_water", sa.String(20)),
    ("timezone", sa.String(50)),
    ("lat", sa.Float),
    ("lng", sa.Float),
)


def upgrade() -> None:
    for name, type_ in COLUMNS:
        op.add_column("tcc_destinations", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _type in COLUMNS:
        op.drop_column("tcc_destinations", name)
