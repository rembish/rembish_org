try:
    from flask_migrate import Migrate
except ImportError:
    class Migrate:
        def __bool__(self):
            return False

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
