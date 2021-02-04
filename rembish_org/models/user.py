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

    @property
    def fullname(self):
        return f"{self.name} {self.surname}"

    @property
    def initials(self):
        if not self.surname:
            return self.name[0].upper()
        return f"{self.name[0]}{self.surname[0]}".upper()

    def __repr__(self):
        return f"<{self.__class__.__name__}#{self.id}: {self.email}>"

    @classmethod
    def get_all_but(cls, me):
        return cls.query.filter(User.id != me.id)

    @classmethod
    def get_by(cls, user_id):
        return cls.query.get(user_id)


class Guest(AnonymousUser):
    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def __bool__(self):
        return False
