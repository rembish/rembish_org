from flask_wtf import FlaskForm
from wtforms import DateField, SelectMultipleField, Form, StringField, BooleanField, FieldList, FormField, HiddenField

from ..libraries.forms import LazySelectField


class CompanionForm(Form):
    user_id = LazySelectField(label="Companion")
    name = StringField(label="Name")
    surname = StringField(label="Surname")
    partial = BooleanField(label="Partial", default=False)


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

    companions = FieldList(FormField(CompanionForm), min_entries=0)
    settlements = FieldList(FormField(SettlementForm), min_entries=1)