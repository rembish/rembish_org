from datetime import datetime
from pkgutil import iter_modules

from flask import Flask, url_for

try:
    from flask_debugtoolbar import DebugToolbarExtension
except ImportError:
    DebugToolbarExtension = lambda app: None

from werkzeug.utils import import_string

from . import blueprints, configuration, commands
from .libraries.authz import security, datastore
from .libraries.database import db, migrate
from .libraries.telegram import telegram
from .models.user import Guest
from .version import __version__


def create_app():
    app = Flask(__name__)
    app.config.from_object(f"{configuration.__name__}.{app.env.title()}Configuration")

    db.init_app(app)
    if migrate:
        migrate.init_app(app, db=db)
    security.init_app(app, datastore=datastore, anonymous_user=Guest, register_blueprint=False)
    telegram.init_app(app)

    if app.debug:
        DebugToolbarExtension(app)

    @app.template_global()
    def static_url(filename):
        return url_for('static', filename=filename)

    @app.context_processor
    def global_variables():
        return {
            "now": datetime.now(),
            "version": f"{__version__}{'+' if app.env == 'development' else ''}",
        }

    for minfo in iter_modules(blueprints.__path__):
        app.register_blueprint(import_string(f"{blueprints.__name__}.{minfo.name}:root"))

    for attribute in dir(commands):
        if not attribute.startswith("__"):
            app.cli.add_command(getattr(commands, attribute))

    return app
