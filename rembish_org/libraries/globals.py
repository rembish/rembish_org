from flask import current_app
from werkzeug.local import LocalProxy

from rembish_org.models.drone import Drone
from rembish_org.models.user import User

me = LocalProxy(lambda: User.query.filter_by(email=current_app.config["ME_EMAIL"]).one())
my_drones = LocalProxy(lambda: Drone.find_by(me))
