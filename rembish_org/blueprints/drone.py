from flask import Blueprint

from ..forms.flight import FlightForm
from ..libraries.globals import me
from ..libraries.templating import with_template, with_json
from ..models.drone import FlightLog

root = Blueprint("drone", __name__)


@root.route("/flightlog")
@with_template
def flightlog():
    flights = FlightLog.get_flights_for(me)

    return {
        "flights": flights,
    }


@root.route("/drones/<int:drone_id>")
@with_template
def drone(drone_id):
    pass


@root.route("/flight/<int:flight_id>")
@with_template
def flight(flight_id):
    pass


@root.route("/flight/new")
@with_template
def new_flight():
    form = FlightForm()
    return {
        "form": form,
    }


@root.route("/flight/takeoff", methods=("POST",))
@with_json
def takeoff():
    pass
