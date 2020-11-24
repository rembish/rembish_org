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


