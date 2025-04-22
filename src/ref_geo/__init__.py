import json
import os
from pathlib import Path

# after drop support of py3.9, replace with from importlib.metadata import entry_point
from backports.entry_points_selectable import entry_points

from flask import Flask, current_app, request
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

from ref_geo.env import db
from ref_geo.routes import routes


migrate = Migrate()


@migrate.configure
def configure_alembic(alembic_config):
    alembic_config.set_main_option("sqlalchemy.url", current_app.config["SQLALCHEMY_DATABASE_URI"])
    version_locations = alembic_config.get_main_option("version_locations", default="").split()
    for entry_point in entry_points(group="alembic", name="migrations"):
        version_locations += [entry_point.value]
    alembic_config.set_main_option("version_locations", " ".join(version_locations))
    return alembic_config


def create_app():
    app = Flask(__name__)

    if "REF_GEO_SETTINGS" in os.environ:
        app.config.from_envvar("REF_GEO_SETTINGS")
    app.config.from_prefixed_env(prefix="REF_GEO")

    db.init_app(app)
    migrate.init_app(app, db, directory=Path(__file__).parent / "migrations")

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        response = e.get_response()
        if request.accept_mimetypes.best == "application/json":
            response.data = json.dumps(
                {
                    "code": e.code,
                    "name": e.name,
                    "description": e.description,
                }
            )
            response.content_type = "application/json"
        return response

    app.register_blueprint(routes, url_prefix="/geo")

    return app
