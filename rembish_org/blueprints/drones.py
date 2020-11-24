from flask import Blueprint

from ..libraries.templating import with_template
from ..models.drone import Drone

root = Blueprint("drones", __name__)


@root.route("/drones")
@with_template
def list():
    pass


@root.route("/drones/<int:drone_id>")
@with_template
def show(drone_id):
    drone = Drone.query.get_or_404(drone_id)
    return {
        "drone": drone,
    }
