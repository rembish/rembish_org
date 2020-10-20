from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length


class ContactForm(FlaskForm):
    name = StringField(label="Your name", validators=[DataRequired(), Length(min=4)])
    email = EmailField(label="Your email", validators=[DataRequired()])
    subject = StringField(label="Subject")
    message = TextAreaField(label="Message", validators=[DataRequired()])

    submit = SubmitField(label="Send message")
