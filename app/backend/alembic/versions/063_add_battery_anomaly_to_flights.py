"""Add battery and anomaly columns to drone_flights.

Per-flight battery telemetry (charge, health, cycles, temp) and
flight anomaly status from pydjirecord.
"""

import sqlalchemy as sa
from alembic import op

revision = "063"
down_revision = "062"


def upgrade() -> None:
    op.add_column(
        "drone_flights",
        sa.Column(
            "battery_id",
            sa.Integer,
            sa.ForeignKey("batteries.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_drone_flights_battery_id", "drone_flights", ["battery_id"])
    op.add_column("drone_flights", sa.Column("anomaly_severity", sa.String(10), nullable=True))
    op.add_column("drone_flights", sa.Column("anomaly_actions", sa.String(500), nullable=True))
    op.add_column("drone_flights", sa.Column("battery_charge_start", sa.Integer, nullable=True))
    op.add_column("drone_flights", sa.Column("battery_charge_end", sa.Integer, nullable=True))
    op.add_column("drone_flights", sa.Column("battery_health_pct", sa.Integer, nullable=True))
    op.add_column("drone_flights", sa.Column("battery_cycles", sa.Integer, nullable=True))
    op.add_column("drone_flights", sa.Column("battery_temp_max", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("drone_flights", "battery_temp_max")
    op.drop_column("drone_flights", "battery_cycles")
    op.drop_column("drone_flights", "battery_health_pct")
    op.drop_column("drone_flights", "battery_charge_end")
    op.drop_column("drone_flights", "battery_charge_start")
    op.drop_column("drone_flights", "anomaly_actions")
    op.drop_column("drone_flights", "anomaly_severity")
    op.drop_index("ix_drone_flights_battery_id", table_name="drone_flights")
    op.drop_column("drone_flights", "battery_id")
