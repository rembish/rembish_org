from flask_security import RoleMixin
from sqlalchemy import PrimaryKeyConstraint

from ..libraries.database import db


class Role(db.Model, RoleMixin):
    __tablename__ = "roles"

    id = db.Column(db.SmallInteger, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<{self.__class__.__name__}#{self.id}: {self.name}>"


roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.SmallInteger(), db.ForeignKey("users.id")),
    db.Column("role_id", db.SmallInteger(), db.ForeignKey("roles.id")),
    PrimaryKeyConstraint("user_id", "role_id")
)
