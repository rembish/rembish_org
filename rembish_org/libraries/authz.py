from flask_security import SQLAlchemyUserDatastore, Security

from .database import db
from ..models.role import Role
from ..models.user import User

datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()
