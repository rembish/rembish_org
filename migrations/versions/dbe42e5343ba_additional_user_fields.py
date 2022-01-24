"""Additional user fields

Revision ID: dbe42e5343ba
Revises: 8339c7e34426
Create Date: 2022-01-24 14:20:03.702838

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dbe42e5343ba'
down_revision = '8339c7e34426'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('surname', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('users', 'name')
    op.drop_column('users', 'surname')
