from flask import Blueprint, request, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.datastructures import MultiDict

from ..forms.trip import TripForm
from ..libraries.database import db
from ..libraries.templating import with_template
from ..models.trip import Trip, TripCompanion, TripSettlement
from ..models.user import User
from ..models.world import Settlement

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
        with db.session.no_autoflush:
            trip = Trip(traveler=current_user)
            for row in form.companions:
                tc = TripCompanion(companion=User.get_by(row.data["user_id"]))
                trip.companions.append(tc)
            for row in form.settlements:
                ts = TripSettlement(settlement=Settlement.get_or_create(**row.data["json"]))
                trip.settlements.append(ts)
            form.populate_obj(trip)
            db.session.add(trip)

        db.session.commit()
        return redirect(url_for("trips.index"))

    print(form.errors)

    return {
        "form": form,
    }
