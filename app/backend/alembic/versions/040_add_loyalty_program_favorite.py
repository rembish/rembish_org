"""Add is_favorite to vault_loyalty_programs

Revision ID: 040
Revises: 039
Create Date: 2026-02-18

Marks one loyalty program per alliance per user as the preferred program
for crediting miles.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "040"
down_revision: Union[str, None] = "039"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vault_loyalty_programs",
        sa.Column("is_favorite", sa.Boolean, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("vault_loyalty_programs", "is_favorite")
