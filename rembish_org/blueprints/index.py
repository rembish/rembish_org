from flask import Blueprint, request, render_template
from markdown2 import markdown_path
from pkg_resources import resource_filename

from ..forms.contact import ContactForm
from ..libraries.telegram import telegram, TelegramError
from ..libraries.templating import with_template, with_json

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
    form = ContactForm()
    return {
        "form": form,
    }


@root.route("/contact/email", methods=("POST",))
@with_json
def email():
    form = ContactForm(request.form)
    if not form.validate_on_submit():
        return {
            "status": 403,
            "errors": form.errors,
        }

    message = render_template("messages/contact.md", **form.data)

    try:
        telegram.send(message, parse_mode="Markdown")
    except TelegramError as tge:
        return {
            "status": tge.code,
            "message": tge.message,
        }
