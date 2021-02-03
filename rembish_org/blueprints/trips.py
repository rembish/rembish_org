from flask import Blueprint, request
from flask_login import login_required
from werkzeug.datastructures import MultiDict

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


@root.route("/trips/add", methods=("GET", "POST"))
@login_required
@with_template
def add():
    data = None

    if request.method == "POST":
        companions = request.form.getlist("companion_ids").copy()
        data = MultiDict()
        i = 0
        for key, value in request.form.items(multi=True):
            if key.startswith("companions-"):
                user_id = key.lstrip("companions-")
                data[f"companions-{i}-user_id"] = user_id
                data[f"companions-{i}-full"] = value
                i += 1
                companions.remove(user_id)
            else:
                data.add(key, value)

        for user_id in companions:
            data[f"companions-{i}-user_id"] = user_id
            i += 1

    form = TripForm(formdata=data)
    if form.validate_on_submit():
        pass

    return {
        "form": form,
    }