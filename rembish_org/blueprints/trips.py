from flask import Blueprint

from ..libraries.templating import with_template

root = Blueprint("trips", __name__)


@root.route("/trips")
@with_template
def index():
    return {}