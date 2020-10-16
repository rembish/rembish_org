from functools import wraps

from flask import Response, request, render_template


def with_template(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        response = function(*args, **kwargs)

        if not isinstance(response, Response):
            template = f"{request.endpoint.replace('.', '/')}.html"
            context = dict(response or {})
            response = render_template(template, **context)

        return response
    return wrapper
