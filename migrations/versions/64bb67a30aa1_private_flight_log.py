"""Private flight log

Revision ID: 64bb67a30aa1
Revises: ffd2fa4da6f7
Create Date: 2020-11-26 12:34:29.491128

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '64bb67a30aa1'
down_revision = 'ffd2fa4da6f7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('drone_flight_log', sa.Column('private', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('drone_flight_log', 'private')
    # ### end Alembic commands ###