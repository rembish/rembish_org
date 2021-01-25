from ..libraries.database import db
from ..libraries.geonames import geonames


class Country(db.Model):
    __tablename__ = "countries"

    id = db.Column(db.SmallInteger, primary_key=True)
    code = db.Column(db.String(2), unique=True, nullable=False)
    geoname_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(255), nullable=False)
    south = db.Column(db.Numeric(10, 8), nullable=False)
    west = db.Column(db.Numeric(11, 8), nullable=False)
    north = db.Column(db.Numeric(10, 8), nullable=False)
    east = db.Column(db.Numeric(11, 8), nullable=False)

    @classmethod
    def get_by(cls, code):
        instance = cls.query.filter_by(code=code).first()
        if instance:
            return instance

        json = geonames.get_country_by(code)
        instance = cls(
            code=json["countryCode"],
            geoname_id=json["geonameId"],
            name=json["countryName"],
            south=json["south"],
            west=json["west"],
            north=json["west"],
            east=json["east"])

        db.session.add(instance)
        db.session.commit()
        return instance


class Settlement(db.Model):
    __tablename__ = "settlements"

    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.String(length=50), unique=True)
    geoname_id = db.Column(db.Integer, nullable=False)

    country_id = db.Column(db.SmallInteger, db.ForeignKey(Country.id), nullable=False)
    country = db.relationship(Country)

    name = db.Column(db.String(255), nullable=False)

    latitude = db.Column(db.Numeric(10, 8), nullable=False)
    longitude = db.Column(db.Numeric(11, 8), nullable=False)