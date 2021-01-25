from flask_security import UserMixin, AnonymousUser

from .role import Role, roles_users
from ..libraries.database import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.SmallInteger, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    surname = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
        Role, secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}#{self.id}: {self.email}>"


class Guest(AnonymousUser):
    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __bool__(self):
        return False
