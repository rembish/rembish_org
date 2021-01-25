from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.dialects import mysql

from ..libraries.database import db


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)

    start_date = db.Column(db.Date, nullable=False, unique=True)
    finish_date = db.Column(db.Date, nullable=True)

    type = db.Column(mysql.SET("tourism", "business", "education", "moving", "other"), default="tourism")
    description = db.Column(db.Text, nullable=True)


trip_companions = db.Table(
    "trip_companions",
    db.Column("trip_id", db.Integer(), db.ForeignKey(Trip.id)),
    db.Column("companion_id", db.SmallInteger(), db.ForeignKey("users.id")),
    PrimaryKeyConstraint("trip_id", "companion_id")
)

trip_settlements = db.Table(
    "trip_settlements",
    db.Column("trip_id", db.Integer(), db.ForeignKey(Trip.id)),
    db.Column("settlement_id", db.Integer(), db.ForeignKey("settlements.id")),
    db.Column("date", db.Date(), nullable=True),
    db.Column("slightly", db.Boolean(), default=False),
    PrimaryKeyConstraint("trip_id", "settlement_id")
)