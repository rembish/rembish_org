"""Default drone

Revision ID: 63c792a00dab
Revises: 2655d07019c7
Create Date: 2020-11-03 09:58:25.652498

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63c792a00dab'
down_revision = '2655d07019c7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('drones', sa.Column('default', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('drones', 'default')
    # ### end Alembic commands ###
