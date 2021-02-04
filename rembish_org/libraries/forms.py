from json import dumps, loads

from wtforms import SelectField, SelectMultipleField, StringField


class LazySelectField(SelectField):
    def __init__(self, label=None, validators=None, coerce=str, choices=None, validate_choice=True, **kwargs):
        super().__init__(
            label=label, validators=validators, coerce=coerce,
            choices=None, validate_choice=validate_choice, **kwargs)

        if callable(choices):
            self.choices = choices

    def iter_choices(self):
        if callable(self.choices):
            self.choices = self.choices()
        yield from super().iter_choices()


class LazySelectMultipleField(SelectMultipleField):
    def __init__(self, label=None, validators=None, coerce=str, choices=None, validate_choice=True, **kwargs):
        super().__init__(
            label=label, validators=validators, coerce=coerce,
            choices=None, validate_choice=validate_choice, **kwargs)

        if callable(choices):
            self.choices = choices

    def iter_choices(self):
        if callable(self.choices):
            self.choices = self.choices()
        yield from super().iter_choices()

    def pre_validate(self, form):
        if callable(self.choices):
            self.choices = self.choices()
        super().pre_validate(form)


class JSONField(StringField):
    def _value(self):
        return dumps(self.data) if self.data else ''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = loads(valuelist[0])
            except ValueError:
                raise ValueError('This field contains invalid JSON')
        else:
            self.data = None

    def pre_validate(self, form):
        super().pre_validate(form)
        if self.data:
            try:
                dumps(self.data)
            except TypeError:
                raise ValueError('This field contains invalid JSON')
