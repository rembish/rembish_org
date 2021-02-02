from functools import cached_property

from flask_wtf import FlaskForm
from wtforms import DateField, SelectMultipleField, Form, StringField, BooleanField, FieldList, FormField, HiddenField, \
    SubmitField

from ..libraries.forms import LazySelectField, LazySelectMultipleField
from ..libraries.globals import me
from ..models.user import User


class CompanionForm(Form):
    user_id = HiddenField()
    full = BooleanField(label="Partial", default=False)

    @cached_property
    def user(self):
        return User.query.get(self.user_id.data)


class SettlementForm(Form):
    date = DateField(label="Day", format="%d.%m.%Y")
    settlement = StringField(label="Settlement")
    slightly = BooleanField(label="Slightly", default=False)


class TripForm(FlaskForm):
    start_date = DateField(label="From", format="%d.%m.%Y")
    finish_date = DateField(label="To", format="%d.%m.%Y")
    type = SelectMultipleField(label="Type", choices=[
        ('tourism', 'Tourism'), ('business', 'Business'), ('education', 'Education'),
        ('moving', 'Moving'), ('other', 'Other'),
    ], default=['tourism'])
    companion_ids = LazySelectMultipleField(
        label="Companions",
        choices=lambda: [(user.id, user.fullname) for user in User.get_all_but(me)]
    )

    companions = FieldList(FormField(CompanionForm), min_entries=0)
    settlements = FieldList(FormField(SettlementForm), min_entries=1)

    add = SubmitField(label="Add")