from os import environ
from importlib import import_module

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow


db_path = environ.get("FLASK_SQLALCHEMY_DB")
if db_path and db_path != f"{__name__}.db":
    db_module_name, db_object_name = db_path.rsplit(".", 1)
    db_module = import_module(db_module_name)
    db = getattr(db_module, db_object_name)
else:
    db = SQLAlchemy()
    environ["FLASK_SQLALCHEMY_DB"] = f"{__name__}.db"


ma_path = environ.get("FLASK_MARSHMALLOW")
if ma_path and ma_path != f"{__name__}.ma":
    ma_module_name, ma_object_name = ma_path.rsplit(".", 1)
    ma_module = import_module(ma_module_name)
    ma = getattr(ma_module, ma_object_name)
else:
    ma = Marshmallow()
    environ["FLASK_MARSHMALLOW"] = f"{__name__}.ma"
    ma.SQLAlchemySchema.OPTIONS_CLASS.session = db.session
    ma.SQLAlchemyAutoSchema.OPTIONS_CLASS.session = db.session


__all__ = ["db", "ma"]
