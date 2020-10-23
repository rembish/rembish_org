from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

from .user import User
from ..libraries.database import db


class OAuth(OAuthConsumerMixin, db.Model):
    __tablename__ = "oauth"

    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.SmallInteger, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)
