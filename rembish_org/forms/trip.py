from flask_wtf import FlaskForm
from wtforms import DateField, SelectMultipleField


class TripForm(FlaskForm):
    start_date = DateField(label="From", format="%d.%m.%Y")
    finish_date = DateField(label="To", format="%d.%m.%Y")
    type = SelectMultipleField(label="Type", choices=[
        ('tourism', 'Tourism'), ('business', 'Business'), ('education', 'Education'),
        ('moving', 'Moving'), ('other', 'Other'),
    ], default=['tourism'])