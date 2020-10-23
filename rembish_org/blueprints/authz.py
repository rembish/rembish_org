from flask import url_for
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.contrib.google import make_google_blueprint
from flask_login import current_user
from flask_security import logout_user, login_user
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import redirect

from ..libraries.database import db
from ..models.oauth import OAuth
from ..models.user import User

storage = SQLAlchemyStorage(OAuth, db.session, user=current_user)
root = make_google_blueprint(scope="https://www.googleapis.com/auth/userinfo.email openid", storage=storage)


@oauth_authorized.connect_via(root)
def google_logged_in(blueprint, token):
    if not token:
        return False

    response = blueprint.session.get("/oauth2/v1/userinfo")
    if not response.ok:
        return False

    info = response.json()
    print(info)
    user_id = info["id"]
    # {'id': 'Integer', 'email': 'Email', 'verified_email': Boolean, 'name': 'Full name', 'given_name': 'Name',
    # 'family_name': 'Surname', 'picture': 'url', 'hd': 'domain'}

    query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=user_id)
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=blueprint.name, provider_user_id=user_id, token=token)

    if not oauth.user:
        query = User.query.filter_by(email=info["email"])
        try:
            oauth.user = query.one()
        except NoResultFound:
            return False

    db.session.add(oauth)
    db.session.commit()
    login_user(oauth.user)
    return False


@oauth_error.connect_via(root)
def google_error(blueprint, error):
    print(error)


@root.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index.index"))
