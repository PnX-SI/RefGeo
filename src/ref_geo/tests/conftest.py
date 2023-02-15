import pytest

from utils_flask_sqla.tests.utils import JSONClient

from ref_geo import create_app
from ref_geo.env import db


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.testing = True
    app.test_client_class = JSONClient
    return app


@pytest.fixture(scope="session")
def _session(app):
    return db.session
