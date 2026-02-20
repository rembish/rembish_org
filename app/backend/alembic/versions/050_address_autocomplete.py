"""Replace structured address fields with single address + add user_id FK

Revision ID: 050
Revises: 049
Create Date: 2026-02-20

Replace line1/line2/city/state/postal_code with a single 'address' text column.
Add optional user_id FK to link addresses to close-one users.
"""

import sqlalchemy as sa
from alembic import op

revision = "050"
down_revision = "049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("vault_addresses", "line1")
    op.drop_column("vault_addresses", "line2")
    op.drop_column("vault_addresses", "city")
    op.drop_column("vault_addresses", "state")
    op.drop_column("vault_addresses", "postal_code")
    op.add_column("vault_addresses", sa.Column("address", sa.Text(), nullable=False))
    op.add_column(
        "vault_addresses",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_addr_user",
        "vault_addresses",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_addr_user", "vault_addresses", type_="foreignkey")
    op.drop_column("vault_addresses", "user_id")
    op.drop_column("vault_addresses", "address")
    op.add_column("vault_addresses", sa.Column("line1", sa.String(200), nullable=False))
    op.add_column("vault_addresses", sa.Column("line2", sa.String(200), nullable=True))
    op.add_column("vault_addresses", sa.Column("city", sa.String(100), nullable=False))
    op.add_column("vault_addresses", sa.Column("state", sa.String(100), nullable=True))
    op.add_column("vault_addresses", sa.Column("postal_code", sa.String(20), nullable=True))
