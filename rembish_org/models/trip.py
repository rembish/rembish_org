from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.dialects import mysql

from .user import User
from .world import Settlement
from ..libraries.database import db


class TripCompanion(db.Model):
    __tablename__ = "trip_companions"

    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), primary_key=True)
    companion_id = db.Column(db.SmallInteger, db.ForeignKey(User.id), primary_key=True)
    partial = db.Column(db.Boolean, default=False)

    companion = db.relationship(User)


class TripSettlement(db.Model):
    __tablename__ = "trip_settlements"

    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), primary_key=True)
    settlement_id = db.Column(db.Integer, db.ForeignKey(Settlement.id), primary_key=True)

    date = db.Column(db.Date, nullable=True)
    slightly = db.Column(db.Boolean, default=False)

    settlement = db.relationship(Settlement)


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    traveler_id = db.Column(db.SmallInteger, db.ForeignKey(User.id), nullable=False)
    traveler = db.relationship(User)

    start_date = db.Column(db.Date, nullable=False, unique=True)
    finish_date = db.Column(db.Date, nullable=True)

    type = db.Column(mysql.SET("tourism", "business", "education", "moving", "other"), default="tourism")
    description = db.Column(db.Text, nullable=True)

    companions = db.relationship(TripCompanion)
    settlements = db.relationship(TripSettlement)
