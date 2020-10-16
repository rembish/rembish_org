from pkgutil import iter_modules

from flask import Flask, url_for
from werkzeug.utils import import_string

from . import blueprints


def create_app():
    app = Flask(__name__)

    @app.template_global()
    def static_url(filename):
        return url_for('static', filename=filename)

    for minfo in iter_modules(blueprints.__path__):
        app.register_blueprint(import_string(f"{blueprints.__name__}.{minfo.name}:root"))

    return app
