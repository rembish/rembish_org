from flask import Blueprint
from markdown2 import markdown_path
from pkg_resources import resource_filename

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


@root.route("/changelog")
@with_template
def changelog():
    filename = resource_filename("rembish_org", "templates/CHANGELOG.md")
    md = markdown_path(filename)
    return {
        "changelog": md,
    }


@root.route("/contact")
@with_template
def contact():
    pass


@root.route("/contact/email", methods=("POST",))
def email():
    pass
