from flask import Blueprint
from flask_login import login_required

from ..forms.trip import TripForm
from ..libraries.templating import with_template

root = Blueprint("trips", __name__)


@root.route("/trips")
@with_template
def map():
    return {}


@root.route("/trips/list")
@with_template
def index():
    return {}


@root.route("/trips/add")
@login_required
@with_template
def add():
    form = TripForm()
    if form.validate_on_submit():
        pass

    return {
        "form": form,
    }