from functools import wraps
from http import HTTPStatus

from flask import request, render_template, jsonify
from werkzeug import Response


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


def with_json(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        response = function(*args, **kwargs) or {}
        if not isinstance(response, dict):
            return response

        status = response.get("status", 200)
        message = response.get("message", HTTPStatus(status).phrase)
        response.update({
            "status": status,
            "message": message,
        })

        json = jsonify(response)
        json.status_code = status

        return json
    return wrapper
