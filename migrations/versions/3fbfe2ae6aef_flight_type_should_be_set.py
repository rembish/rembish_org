"""Flight type should be set

Revision ID: 3fbfe2ae6aef
Revises: 48b8855c4601
Create Date: 2020-11-10 20:04:14.735427

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '3fbfe2ae6aef'
down_revision = '48b8855c4601'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('drone_flight_log', 'type')
    op.add_column('drone_flight_log', sa.Column('type', mysql.SET("photo", "video", "training"), nullable=True, default="photo"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('drone_flight_log', 'type')
    op.add_column('drone_flight_log', sa.Column('type', mysql.VARCHAR(length=100), nullable=True))
    # ### end Alembic commands ###