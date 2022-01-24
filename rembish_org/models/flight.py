from sqlalchemy.dialects import mysql

from .drone import Drone
from .trip import Trip
from .world import Country
from ..libraries.database import db


class FlightLog(db.Model):
    __tablename__ = "drone_flight_log"

    id = db.Column(db.Integer, primary_key=True)
    private = db.Column(db.Boolean, default=False)

    drone_id = db.Column(db.SmallInteger, db.ForeignKey(Drone.id), nullable=False)
    drone = db.relationship(Drone)

    country_id = db.Column(db.SmallInteger, db.ForeignKey(Country.id))
    country = db.relationship(Country)

    trip_id = db.Column(db.Integer, db.ForeignKey(Trip.id), nullable=True)
    trip = db.relationship(Trip)

    date = db.Column(db.Date, nullable=False, server_default=db.text("(CURRENT_DATE)"))
    in_air = db.Column(db.Boolean, default=False)

    location = db.Column(db.String(length=200))
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)
    place_id = db.Column(db.String(length=50))

    takeoffs = db.relationship(
        "Takeoff", lazy="select", backref=db.backref("flight", lazy="joined"), cascade="all, delete")

    type = db.Column(mysql.SET("photo", "video", "training"), default="photo")
    activity = db.Column(db.String(length=100))
    description = db.Column(db.String(length=200))

    @classmethod
    def get_flights_for(cls, user, private=False):
        result = []
        for flight in db.session.execute("""
            SELECT 
                dfl.*,  c.code  AS `country_code`, c.name AS `country`,
                COALESCE(d.callsign, d.nickname, CONCAT(dv.name, '', dm.name)) AS `drone_name`,
                MIN(dt.start) AS `takeoff`, 
                MAX(dt.finish) AS `landing`,
                MAX(dt.altitude) AS `altitude`,
                SUM(dt.distance) AS `distance`,
                SEC_TO_TIME(SUM(TIME_TO_SEC(TIMEDIFF(dt.finish, dt.start)))) AS `duration`,
                COUNT(dt.flight_id) AS `landing_count`
            FROM drone_flight_log AS dfl
            JOIN drone_takeoffs AS dt ON dt.flight_id = dfl.id
            JOIN drones AS d ON d.id = dfl.drone_id
            JOIN drone_models AS dm ON dm.id = d.model_id
            JOIN drone_vendors AS dv ON dv.id = dm.vendor_id
            JOIN countries AS c ON c.id = dfl.country_id
            WHERE
                d.owner_id = :owner_id AND dfl.private IN (0, :private)
            GROUP BY dt.flight_id
            ORDER BY dfl.date DESC, dt.start DESC
        """, {"owner_id": user.id, "private": int(private)}):
            row = dict(flight)
            row["type"] = row["type"].split(",") if row["type"] else []
            result.append(row)

        return result

    @classmethod
    def get_statistics_for(cls, user):
        response = db.session.execute("""
            SELECT
                COUNT(DISTINCT dfl.id) AS `flight_count`,
                COUNT(DISTINCT dt.id) AS `takeoff_count`,
                COUNT(DISTINCT dfl.place_id) AS `place_count`,
                COUNT(DISTINCT dfl.country_id) AS `country_count`,
                COUNT(DISTINCT d.id) AS `drone_count`,
                SUM(dt.distance) AS `distance`,
                MAX(dt.altitude) AS `altitude`,
                SEC_TO_TIME(SUM(TIME_TO_SEC(TIMEDIFF(dt.finish, dt.start)))) AS `duration`,
                DATEDIFF(MAX(dfl.date), MIN(dfl.date)) AS `days`
            FROM drone_flight_log AS dfl
            JOIN drone_takeoffs AS dt ON dt.flight_id = dfl.id
            JOIN drones AS d ON d.id = dfl.drone_id
            WHERE d.owner_id = :owner_id
        """, {"owner_id": user.id})
        for row in response:
            return row


class Takeoff(db.Model):
    __tablename__ = "drone_takeoffs"

    id = db.Column(db.Integer, primary_key=True)

    flight_id = db.Column(db.Integer, db.ForeignKey(FlightLog.id), nullable=False)

    start = db.Column(db.Time, nullable=False, server_default=db.text("(CURRENT_DATE)"))
    finish = db.Column(db.Time)
    distance = db.Column(db.Integer)
    altitude = db.Column(db.Integer)
