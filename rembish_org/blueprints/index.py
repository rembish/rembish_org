from flask import Blueprint

from ..libraries.templating import with_template

root = Blueprint('index', __name__)


@root.route("/")
@with_template
def index():
    pass


@root.route("/resume")
@with_template
def resume():
    pass


@root.route("/contacts")
@with_template
def contacts():
    pass
