"""Partial companionship

Revision ID: f43e8b3911e3
Revises: 8c67c1445bfe
Create Date: 2021-01-26 20:21:28.811584

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f43e8b3911e3'
down_revision = '8c67c1445bfe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trip_companions', sa.Column('partial', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trip_companions', 'partial')
    # ### end Alembic commands ###
