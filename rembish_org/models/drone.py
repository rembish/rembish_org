from .user import User
from ..libraries.database import db


class Vendor(db.Model):
    __tablename__ = "drone_vendors"

    id = db.Column(db.SmallInteger, primary_key=True)
    name = db.Column(db.String(length=50), nullable=False)
    url = db.Column(db.String(length=200))


class Model(db.Model):
    __tablename__ = "drone_models"

    id = db.Column(db.SmallInteger, primary_key=True)
    vendor_id = db.Column(db.SmallInteger, db.ForeignKey(Vendor.id), nullable=False)
    vendor = db.relationship(Vendor)

    name = db.Column(db.String(length=100), nullable=False)
    url = db.Column(db.String(length=200))


class Drone(db.Model):
    __tablename__ = "drones"

    id = db.Column(db.SmallInteger, primary_key=True)

    owner_id = db.Column(db.SmallInteger, db.ForeignKey(User.id), nullable=False)
    owner = db.relationship(User)

    model_id = db.Column(db.SmallInteger, db.ForeignKey(Model.id), nullable=False)
    model = db.relationship(Model)

    nickname = db.Column(db.String(length=100))
    serial = db.Column(db.String(length=100), nullable=False)
    callsign = db.Column(db.String(length=20))

    default = db.Column(db.Boolean, default=False, nullable=False)

    def __str__(self):
        return f"{self.model.vendor.name} {self.model.name} ({self.callsign or self.serial or self.nickname})"

    @property
    def name(self):
        if self.callsign:
            return self.callsign
        if self.nickname:
            return self.nickname
        return f"{self.model.vendor.name} {self.model.name}"

    @classmethod
    def find_by(cls, owner):
        return cls.query.filter_by(owner=owner).order_by(cls.default.desc()).all()


class FlightLog(db.Model):
    __tablename__ = "drone_flight_log"

    id = db.Column(db.Integer, primary_key=True)

    drone_id = db.Column(db.SmallInteger, db.ForeignKey(Drone.id), nullable=False)
    drone = db.relationship(Drone)

    date = db.Column(db.Date, nullable=False, server_default=db.text("NOW()"))
    in_air = db.Column(db.Boolean, default=False)

    location = db.Column(db.String(length=200))
    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)

    takeoffs = db.relationship("Takeoff", lazy="select", backref=db.backref("flight", lazy="joined"))

    type = db.Column(db.String(length=100))
    activity = db.Column(db.String(length=100))
    description = db.Column(db.String(length=200))

    @classmethod
    def get_flights_for(cls, user):
        return db.session.execute("""
            SELECT 
                dfl.*, 
                COALESCE(d.callsign, d.nickname, CONCAT(dv.name, '', dm.name)) AS `drone_name`,
                MIN(dt.start) AS `takeoff`, 
                MAX(dt.finish) AS `landing`,
                SEC_TO_TIME(SUM(TIME_TO_SEC(TIMEDIFF(dt.finish, dt.start)))) AS `duration`,
                COUNT(dt.flight_id) AS `landing_count`
            FROM drone_flight_log AS dfl
            JOIN drone_takeoffs AS dt ON dt.flight_id = dfl.id
            JOIN drones AS d ON d.id = dfl.drone_id
            JOIN drone_models AS dm ON dm.id = d.model_id
            JOIN drone_vendors AS dv ON dv.id = dm.vendor_id
            WHERE
                d.owner_id = :owner_id
            GROUP BY dt.flight_id
            ORDER BY dfl.date DESC, dt.start DESC
        """, {"owner_id": user.id})


class Takeoff(db.Model):
    __tablename__ = "drone_takeoffs"

    id = db.Column(db.Integer, primary_key=True)

    flight_id = db.Column(db.Integer, db.ForeignKey(FlightLog.id), nullable=False)

    start = db.Column(db.Time, nullable=False, server_default=db.text("NOW()"))
    finish = db.Column(db.Time)
    distance = db.Column(db.Integer)
