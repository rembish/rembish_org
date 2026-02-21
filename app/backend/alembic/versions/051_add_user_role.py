"""Replace is_admin boolean with role column

Revision ID: 051
Revises: 050
Create Date: 2026-02-21

Replace is_admin boolean with a role VARCHAR(20) column.
Existing admins get role='admin', others get NULL.
"""

import sqlalchemy as sa
from alembic import op

revision = "051"
down_revision = "050"


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(20), nullable=True))
    op.execute("UPDATE users SET role = 'admin' WHERE is_admin = 1")
    op.drop_column("users", "is_admin")


def downgrade() -> None:
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), server_default=sa.text("0")))
    op.execute("UPDATE users SET is_admin = 1 WHERE role = 'admin'")
    op.drop_column("users", "role")
