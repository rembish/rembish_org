from flask import Blueprint

from ..libraries.templating import with_template

root = Blueprint('index', __name__)


@root.route("/")
@with_template
def index():
    pass


@root.route("/resume")
def resume():
    pass


@root.route("/contacts")
def contacts():
    pass
