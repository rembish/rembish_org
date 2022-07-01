from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, StringField, TextAreaField, Form, TimeField, FieldList, \
    FormField, SubmitField, SelectMultipleField, HiddenField, BooleanField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import HiddenInput

from ..libraries.forms import LazySelectField
from ..libraries.globals import my_drones


class TakeoffForm(Form):
    start = TimeField(label="Take-off", format="%H:%M:%S", validators=[DataRequired()])
    finish = TimeField(label="Landing", format="%H:%M:%S", validators=[Optional(strip_whitespace=True)])
    distance = IntegerField(label="Distance", validators=[Optional(strip_whitespace=True)])
    altitude = IntegerField(label="Altitude", validators=[Optional(strip_whitespace=True)])


class FlightForm(FlaskForm):
    date = DateField(label="Date", default=date.today(), format="%d.%m.%Y")
    drone_id = LazySelectField(
        label="Drone",
        choices=lambda: [(drone.id, drone) for drone in my_drones], default=lambda: my_drones[0].id,
        validators=[DataRequired()])
    location = StringField(label="Location")
    place_id = HiddenField(validators=[Optional(strip_whitespace=True)])
    latitude = DecimalField(widget=HiddenInput(), validators=[DataRequired()])
    longitude = DecimalField(widget=HiddenInput(), validators=[DataRequired()])
    type = SelectMultipleField(label="Type", choices=[
        ('photo', 'Photo'), ('video', 'Video'), ('training', 'Training'),
    ], default=['photo'])
    activity = StringField(label="Activity", validators=[Optional(strip_whitespace=True)])
    description = TextAreaField(label="Additional information", validators=[Optional(strip_whitespace=True)])
    takeoffs = FieldList(FormField(TakeoffForm), min_entries=1)
    private = BooleanField(label="Is private?", default=False)
    register = SubmitField(label="Register")
