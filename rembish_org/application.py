from datetime import datetime
from pkgutil import iter_modules

from flask import Flask, url_for

try:
    from flask_debugtoolbar import DebugToolbarExtension
except ImportError:
    DebugToolbarExtension = lambda app: None

from werkzeug.utils import import_string

from . import blueprints, configuration


def create_app():
    app = Flask(__name__)
    app.config.from_object(f"{configuration.__name__}.{app.env.title()}Configuration")

    if app.debug:
        DebugToolbarExtension(app)

    @app.template_global()
    def static_url(filename):
        return url_for('static', filename=filename)

    @app.context_processor
    def global_variables():
        return {
            "now": datetime.now()
        }

    for minfo in iter_modules(blueprints.__path__):
        app.register_blueprint(import_string(f"{blueprints.__name__}.{minfo.name}:root"))

    return app
