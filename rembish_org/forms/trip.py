from functools import cached_property

from flask_wtf import FlaskForm
from wtforms import DateField, SelectMultipleField, Form, StringField, BooleanField, FieldList, FormField, \
    SubmitField, TextAreaField, IntegerField
from wtforms.validators import Optional, DataRequired
from wtforms.widgets import HiddenInput

from ..libraries.forms import LazySelectMultipleField, JSONField
from ..libraries.globals import me
from ..models.user import User


class CompanionForm(Form):
    user_id = IntegerField(widget=HiddenInput())
    full = BooleanField(default=False)

    @cached_property
    def user(self):
        return User.query.get(self.user_id.data)


class SettlementForm(Form):
    date = DateField(label="Day", format="%d.%m.%Y", validators=[Optional()])
    location = StringField(label="Location")
    json = JSONField(validators=[DataRequired()], widget=HiddenInput())
    slightly = BooleanField(default=False)


class TripForm(FlaskForm):
    start_date = DateField(label="From", format="%d.%m.%Y", validators=[DataRequired()])
    finish_date = DateField(label="To", format="%d.%m.%Y", validators=[Optional()])
    type = SelectMultipleField(label="Type", choices=[
        ('tourism', 'Tourism'), ('business', 'Business'), ('education', 'Education'),
        ('moving', 'Moving'), ('other', 'Other'),
    ], default=['tourism'], validators=[DataRequired()])
    companion_ids = LazySelectMultipleField(
        label="Companions", coerce=int,
        choices=lambda: [(user.id, user.fullname) for user in User.get_all_but(me)]
    )

    companions = FieldList(FormField(CompanionForm), min_entries=0)
    settlements = FieldList(FormField(SettlementForm), min_entries=1)

    description = TextAreaField(label="Description", validators=[Optional(strip_whitespace=True)])

    add = SubmitField(label="Add")
