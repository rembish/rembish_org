from flask import Blueprint, redirect, url_for

from ..forms.flight import FlightForm
from ..libraries.database import db
from ..libraries.geonames import geonames
from ..libraries.globals import me
from ..libraries.templating import with_template, with_json
from ..models.flight import FlightLog, Takeoff
from ..models.world import Country

root = Blueprint("flights", __name__)


@root.route("/flights")
@with_template
def map():
    pass


@root.route("/flights/log")
@with_template
def log():
    flights = FlightLog.get_flights_for(me)
    stats = FlightLog.get_statistics_for(me)

    return {
        "flights": flights,
        "stats": stats,
    }


@root.route("/flights/<int:flight_id>")
@with_template
def show(flight_id):
    flight = FlightLog.query.get_or_404(flight_id)
    return {
        "flight": flight,
    }


@root.route("/flights/new", methods=("GET", "POST"))
@with_template
def new():
    form = FlightForm()
    if form.validate_on_submit():
        flight = FlightLog()
        for _ in form.takeoffs:
            flight.takeoffs.append(Takeoff())
        form.populate_obj(flight)

        code = geonames.get_code_by(flight.latitude, flight.longitude)
        if code:
            country = Country.get_by(code)
            flight.country = country

        db.session.add(flight)
        db.session.commit()

        return redirect(url_for("flights.log"))

    return {
        "form": form,
    }


@root.route("/flights/takeoff", methods=("POST",))
@with_json
def takeoff():
    pass
