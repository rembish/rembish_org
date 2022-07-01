from flask import Blueprint, request, render_template
from flask_dance.contrib.google import google
from flask_login import current_user
from markdown2 import markdown_path
from oauthlib.oauth2 import InvalidClientIdError
from pkg_resources import resource_filename

from ..forms.contact import ContactForm
from ..libraries.telegram import telegram, TelegramError
from ..libraries.templating import with_template, with_json

root = Blueprint('index', __name__)


@root.route("/")
@with_template
def index():
    pass


@root.route("/cv")
@with_template
def cv():
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
    info = {}
    if current_user and google.authorized:
        try:
            response = google.get("/oauth2/v1/userinfo")
            if response.ok:
                info = response.json()
        except InvalidClientIdError:
            pass

    form = ContactForm(data=info)
    return {
        "form": form,
    }


@root.route("/contact/message", methods=("POST",))
@with_json
def message():
    form = ContactForm(request.form)
    if not form.validate_on_submit():
        return {
            "status": 403,
            "errors": form.errors,
        }

    text = render_template("messages/contact.md", **form.data)

    try:
        telegram.send(text, parse_mode="Markdown")
    except TelegramError as tge:
        return {
            "status": tge.code,
            "message": tge.message,
        }
