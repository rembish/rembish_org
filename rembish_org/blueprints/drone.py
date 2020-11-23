from flask import Blueprint, redirect, url_for

from ..forms.flight import FlightForm
from ..libraries.database import db
from ..libraries.globals import me
from ..libraries.templating import with_template, with_json
from ..models.drone import FlightLog, Takeoff

root = Blueprint("drone", __name__)


@root.route("/flightlog")
@with_template
def flightlog():
    flights = FlightLog.get_flights_for(me)
    stats = FlightLog.get_statistics_for(me)

    return {
        "flights": flights,
        "stats": stats,
    }


@root.route("/drones/<int:drone_id>")
@with_template
def drone(drone_id):
    pass


@root.route("/flight/<int:flight_id>")
@with_template
def flight(flight_id):
    pass


@root.route("/flight/new", methods=("GET", "POST"))
@with_template
def new_flight():
    form = FlightForm()
    if form.validate_on_submit():
        flightlog = FlightLog()
        for _ in form.takeoffs:
            flightlog.takeoffs.append(Takeoff())
        form.populate_obj(flightlog)

        db.session.add(flightlog)
        db.session.commit()

        return redirect(url_for("drone.flightlog"))

    return {
        "form": form,
    }


@root.route("/flight/takeoff", methods=("POST",))
@with_json
def takeoff():
    pass
