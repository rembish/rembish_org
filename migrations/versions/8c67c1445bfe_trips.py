"""Trips

Revision ID: 8c67c1445bfe
Revises: 64bb67a30aa1
Create Date: 2021-01-25 21:04:04.426989

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '8c67c1445bfe'
down_revision = '64bb67a30aa1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('trips',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('finish_date', sa.Date(), nullable=True),
    sa.Column('type', mysql.SET("tourism", "business", "education", "moving", "other"), default="tourism", nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('start_date')
    )
    op.create_table('settlements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('place_id', sa.String(length=50), nullable=True),
    sa.Column('geoname_id', sa.Integer(), nullable=False),
    sa.Column('country_id', sa.SmallInteger(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=False),
    sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=False),
    sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('place_id')
    )
    op.create_table('trip_companions',
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('companion_id', sa.SmallInteger(), nullable=False),
    sa.ForeignKeyConstraint(['companion_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
    sa.PrimaryKeyConstraint('trip_id', 'companion_id')
    )
    op.create_table('trip_settlements',
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('settlement_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('slightly', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['settlement_id'], ['settlements.id'], ),
    sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
    sa.PrimaryKeyConstraint('trip_id', 'settlement_id')
    )
    op.add_column('drone_flight_log', sa.Column('trip_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'drone_flight_log', 'trips', ['trip_id'], ['id'])
    op.add_column('users', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('surname', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'surname')
    op.drop_column('users', 'name')
    op.drop_constraint(None, 'drone_flight_log', type_='foreignkey')
    op.drop_column('drone_flight_log', 'trip_id')
    op.drop_table('trip_settlements')
    op.drop_table('trip_companions')
    op.drop_table('settlements')
    op.drop_table('trips')
    # ### end Alembic commands ###
