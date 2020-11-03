from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, StringField, TextAreaField, Form, TimeField, FloatField, FieldList, \
    FormField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired

from ..libraries.forms import LazySelectField
from ..libraries.globals import my_drones


class TakeoffForm(Form):
    start = TimeField(label="Take-off")
    duration = TimeField(label="Duration")
    distance = FloatField(label="Distance")


class FlightForm(FlaskForm):
    date = DateField(label="Date", default=date.today(), format="%d.%m.%Y")
    drone = LazySelectField(
        label="Drone",
        choices=lambda: [(drone.id, drone) for drone in my_drones], default=lambda: my_drones[0].id,
        validators=[DataRequired()])
    location = StringField(label="Location")
    gps = StringField(label="GPS coordinates", validators=[DataRequired()])
    type = SelectMultipleField(label="Type", choices=[
        ('photo', 'Photo'), ('video', 'Video'), ('training', 'Training'),
    ], default=['photo'])
    activity = StringField(label="Activity")
    description = TextAreaField(label="Additional information")
    takeoffs = FieldList(FormField(TakeoffForm), min_entries=1)
    register = SubmitField(label="Register")

