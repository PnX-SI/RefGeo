from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey
from sqlalchemy.orm import deferred, column_property
from sqlalchemy.sql import func

from sqlalchemy.dialects.postgresql import JSONB

from utils_flask_sqla.serializers import serializable
from utils_flask_sqla_geo.serializers import geoserializable

from ref_geo.env import db

from sqlalchemy.ext.hybrid import hybrid_property


@serializable
class BibAreasTypes(db.Model):
    __tablename__ = "bib_areas_types"
    __table_args__ = {"schema": "ref_geo"}
    id_type = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.Unicode)
    type_code = db.Column(db.Unicode)
    type_desc = db.Column(db.Unicode)
    ref_name = db.Column(db.Unicode)
    ref_version = db.Column(db.Integer)
    num_version = db.Column(db.Unicode)
    size_hierarchy = db.Column(db.Integer)


cor_areas = db.Table(
    "cor_areas",
    db.Column(
        "id_area_group",
        db.Integer,
        ForeignKey("ref_geo.l_areas.id_area"),
        primary_key=True,
    ),
    db.Column(
        "id_area",
        db.Integer,
        ForeignKey("ref_geo.l_areas.id_area"),
        primary_key=True,
    ),
    schema="ref_geo",
)


@geoserializable
class LAreas(db.Model):
    __tablename__ = "l_areas"
    __table_args__ = {"schema": "ref_geo"}
    id_area = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.Integer, ForeignKey("ref_geo.bib_areas_types.id_type"))
    area_name = db.Column(db.Unicode)
    area_code = db.Column(db.Unicode)
    geom = db.Column(Geometry("MULTIPOLYGON"))
    centroid = db.Column(Geometry("POINT"))
    geom_4326 = deferred(db.Column(Geometry("MULTIPOLYGON", 4326)))
    source = db.Column(db.Unicode)
    enable = db.Column(db.Boolean, nullable=False, default=True)
    meta_create_date = db.Column(db.DateTime, default=datetime.now)
    meta_update_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    description = db.Column(db.UnicodeText)
    area_type = db.relationship("BibAreasTypes", lazy="select")
    parent_areas = db.relationship(
        "LAreas",
        secondary=cor_areas,
        primaryjoin=id_area == cor_areas.c.id_area,
        secondaryjoin=cor_areas.c.id_area_group == id_area,
        backref="child_areas",
        lazy="raise",
    )


@serializable
class BibLinearsTypes(db.Model):
    __tablename__ = "bib_linears_types"
    __table_args__ = {"schema": "ref_geo"}
    id_type = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.Unicode(length=200), nullable=False)
    type_code = db.Column(db.Unicode(length=25), nullable=False)
    type_desc = db.Column(db.Unicode)
    ref_name = db.Column(db.Unicode(length=200))
    ref_version = db.Column(db.Integer)
    num_version = db.Column(db.Unicode(length=50))


cor_linear_group = db.Table(
    "cor_linear_group",
    db.Column(
        "id_group",
        db.Integer,
        ForeignKey("ref_geo.t_linear_groups.id_group"),
        primary_key=True,
    ),
    db.Column(
        "id_linear",
        db.Integer,
        ForeignKey("ref_geo.l_linears.id_linear"),
        primary_key=True,
    ),
    schema="ref_geo",
)


cor_linear_area = db.Table(
    "cor_linear_area",
    db.Column(
        "id_area",
        db.Integer,
        ForeignKey("ref_geo.l_areas.id_area"),
        primary_key=True,
    ),
    db.Column(
        "id_linear",
        db.Integer,
        ForeignKey("ref_geo.l_linears.id_linear"),
        primary_key=True,
    ),
    schema="ref_geo",
)


@geoserializable
class LLinears(db.Model):
    __tablename__ = "l_linears"
    __table_args__ = {"schema": "ref_geo"}
    id_linear = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(
        db.Integer, ForeignKey("ref_geo.bib_linears_types.id_type"), nullable=False
    )
    linear_name = db.Column(db.Unicode(length=250))
    linear_code = db.Column(db.Unicode(length=25))
    geom = db.Column(Geometry("GEOMETRY"))
    source = db.Column(db.Unicode(length=250))
    enable = db.Column(db.Boolean, nullable=False, default=True)
    additional_data = db.Column(JSONB)
    meta_create_date = db.Column(db.DateTime, default=datetime.now)
    meta_update_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    type = db.relationship("BibLinearsTypes")
    groups = db.relationship(
        "TLinearGroups", secondary=cor_linear_group, backref="linears", lazy="raise"
    )
    areas = db.relationship("LAreas", secondary=cor_linear_area, backref="linears", lazy="raise")


@serializable
class TLinearGroups(db.Model):
    __table_name__ = "t_linear_groups"
    __table_args__ = {"schema": "ref_geo"}
    id_group = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(length=250))
    code = db.Column(db.Unicode(length=25), unique=True)


@serializable
class BibPointsTypes(db.Model):
    __tablename__ = "bib_points_types"
    __table_args__ = {"schema": "ref_geo"}
    id_type = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.Unicode(length=200), nullable=False)
    type_code = db.Column(db.Unicode(length=25), nullable=False)
    type_desc = db.Column(db.Unicode)
    ref_name = db.Column(db.Unicode(length=200))
    ref_version = db.Column(db.Integer)
    num_version = db.Column(db.Unicode(length=50))


@geoserializable
class LPoints(db.Model):
    __tablename__ = "l_points"
    __table_args__ = {"schema": "ref_geo"}
    id_point = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.Integer, ForeignKey("ref_geo.bib_points_types.id_type"), nullable=False)
    point_name = db.Column(db.Unicode(length=250))
    point_code = db.Column(db.Unicode(length=25))
    geom = db.Column(Geometry("GEOMETRY"))
    source = db.Column(db.Unicode(length=250))
    enable = db.Column(db.Boolean, nullable=False, default=True)
    additional_data = db.Column(JSONB)
    meta_create_date = db.Column(db.DateTime, default=datetime.now)
    meta_update_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    type = db.relationship("BibPointsTypes")

    geom_4326 = column_property(
        func.ST_TRANSFORM(geom, 4326),
        deferred=True,
    )


@serializable
class LiMunicipalities(db.Model):
    __tablename__ = "li_municipalities"
    __table_args__ = {"schema": "ref_geo"}
    id_municipality = db.Column(db.String(25), primary_key=True)
    id_area = db.Column(db.Integer)
    status = db.Column(db.Unicode)
    insee_com = db.Column(db.Unicode)
    nom_com = db.Column(db.Unicode)
    insee_arr = db.Column(db.Unicode)
    nom_dep = db.Column(db.Unicode)
    insee_dep = db.Column(db.Unicode)
    nom_reg = db.Column(db.Unicode)
    insee_reg = db.Column(db.Unicode)
    code_epci = db.Column(db.Unicode)
    plani_precision = db.Column(db.Float)
    siren_code = db.Column(db.Unicode)
    canton = db.Column(db.Unicode)
    population = db.Column(db.Integer)
    multican = db.Column(db.Unicode)
    cc_nom = db.Column(db.Unicode)
    cc_siren = db.Column(db.BigInteger)
    cc_nature = db.Column(db.Unicode)
    cc_date_creation = db.Column(db.Unicode)
    cc_date_effet = db.Column(db.Unicode)
    insee_commune_nouvelle = db.Column(db.Unicode)
    meta_create_date = db.Column(db.DateTime)
    meta_update_date = db.Column(db.DateTime)

    @hybrid_property
    def nom_com_dept(self):
        return "{} ({})".format(self.nom_com, self.insee_dep)
