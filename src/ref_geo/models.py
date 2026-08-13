from datetime import datetime
from sqlalchemy import (
    ForeignKey,
    func,
    Integer,
    Unicode,
    Boolean,
    DateTime,
    BigInteger,
    Table,
    Column,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    deferred,
    column_property,
    relationship,
)
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB
from utils_flask_sqla.serializers import serializable
from utils_flask_sqla_geo.serializers import geoserializable
from sqlalchemy.ext.hybrid import hybrid_property
from ref_geo.env import db


@serializable
class BibAreasTypes(db.Model):
    __tablename__ = "bib_areas_types"
    __table_args__ = {"schema": "ref_geo"}
    id_type: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_name: Mapped[str]
    type_code: Mapped[str]
    type_desc: Mapped[str]
    ref_name: Mapped[str]
    ref_version: Mapped[int]
    num_version: Mapped[str]
    size_hierarchy: Mapped[int]


cor_areas = Table(
    "cor_areas",
    db.metadata,
    Column("id_area_group", Integer, ForeignKey("ref_geo.l_areas.id_area"), primary_key=True),
    Column("id_area", Integer, ForeignKey("ref_geo.l_areas.id_area"), primary_key=True),
    schema="ref_geo",
)


@geoserializable
class LAreas(db.Model):
    __tablename__ = "l_areas"
    __table_args__ = {"schema": "ref_geo"}
    id_area: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_type: Mapped[int] = mapped_column(Integer, ForeignKey("ref_geo.bib_areas_types.id_type"))
    area_name: Mapped[str]
    area_code: Mapped[str]
    geom: Mapped[Geometry] = mapped_column(Geometry("MULTIPOLYGON"))
    centroid: Mapped[Geometry] = mapped_column(Geometry("POINT"))
    geom_4326 = deferred(mapped_column(Geometry("MULTIPOLYGON", 4326)))
    source: Mapped[str]
    enable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta_create_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    meta_update_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    description: Mapped[str]
    area_type: Mapped["BibAreasTypes"] = relationship("BibAreasTypes", lazy="select")
    parent_areas: Mapped[list["LAreas"]] = relationship(
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
    id_type: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_name: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    type_code: Mapped[str] = mapped_column(Unicode(25), nullable=False)
    type_desc: Mapped[str]
    ref_name: Mapped[str] = mapped_column(Unicode(200))
    ref_version: Mapped[int]
    num_version: Mapped[str] = mapped_column(Unicode(50))


cor_linear_group = Table(
    "cor_linear_group",
    db.metadata,
    Column("id_group", Integer, ForeignKey("ref_geo.t_linear_groups.id_group"), primary_key=True),
    Column("id_linear", Integer, ForeignKey("ref_geo.l_linears.id_linear"), primary_key=True),
    schema="ref_geo",
)

cor_linear_area = Table(
    "cor_linear_area",
    db.metadata,
    Column("id_area", Integer, ForeignKey("ref_geo.l_areas.id_area"), primary_key=True),
    Column("id_linear", Integer, ForeignKey("ref_geo.l_linears.id_linear"), primary_key=True),
    schema="ref_geo",
)


@geoserializable
class LLinears(db.Model):
    __tablename__ = "l_linears"
    __table_args__ = {"schema": "ref_geo"}
    id_linear: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_type: Mapped[int] = mapped_column(
        Integer, ForeignKey("ref_geo.bib_linears_types.id_type"), nullable=False
    )
    linear_name: Mapped[str] = mapped_column(Unicode(250))
    linear_code: Mapped[str] = mapped_column(Unicode(25))
    geom: Mapped[Geometry] = mapped_column(Geometry("GEOMETRY"))
    source: Mapped[str] = mapped_column(Unicode(250))
    enable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    additional_data: Mapped[dict] = mapped_column(JSONB)
    meta_create_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    meta_update_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    type: Mapped["BibLinearsTypes"] = relationship("BibLinearsTypes")
    groups: Mapped[list["TLinearGroups"]] = relationship(
        "TLinearGroups", secondary=cor_linear_group, backref="linears", lazy="raise"
    )
    areas: Mapped[list["LAreas"]] = relationship(
        "LAreas", secondary=cor_linear_area, backref="linears", lazy="raise"
    )


@serializable
class TLinearGroups(db.Model):
    __tablename__ = "t_linear_groups"
    __table_args__ = {"schema": "ref_geo"}
    id_group: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(250))
    code: Mapped[str] = mapped_column(Unicode(25), unique=True)


@serializable
class BibPointsTypes(db.Model):
    __tablename__ = "bib_points_types"
    __table_args__ = {"schema": "ref_geo"}
    id_type: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_name: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    type_code: Mapped[str] = mapped_column(Unicode(25), nullable=False)
    type_desc: Mapped[str]
    ref_name: Mapped[str] = mapped_column(Unicode(200))
    ref_version: Mapped[int]
    num_version: Mapped[str] = mapped_column(Unicode(50))


@geoserializable
class LPoints(db.Model):
    __tablename__ = "l_points"
    __table_args__ = {"schema": "ref_geo"}
    id_point: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_type: Mapped[int] = mapped_column(
        Integer, ForeignKey("ref_geo.bib_points_types.id_type"), nullable=False
    )
    point_name: Mapped[str] = mapped_column(Unicode(250))
    point_code: Mapped[str] = mapped_column(Unicode(25))
    geom: Mapped[Geometry] = mapped_column(Geometry("GEOMETRY"))
    source: Mapped[str] = mapped_column(Unicode(250))
    enable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    additional_data: Mapped[dict] = mapped_column(JSONB)
    meta_create_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    meta_update_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    type: Mapped["BibPointsTypes"] = relationship("BibPointsTypes")

    geom_4326 = column_property(
        func.ST_Transform(geom, 4326),
        deferred=True,
    )


@serializable
class LiMunicipalities(db.Model):
    __tablename__ = "li_municipalities"
    __table_args__ = {"schema": "ref_geo"}
    id_municipality: Mapped[str] = mapped_column(Unicode(25), primary_key=True)
    id_area: Mapped[int]
    status: Mapped[str]
    insee_com: Mapped[str]
    nom_com: Mapped[str]
    insee_arr: Mapped[str]
    nom_dep: Mapped[str]
    insee_dep: Mapped[str]
    nom_reg: Mapped[str]
    insee_reg: Mapped[str]
    code_epci: Mapped[str]
    plani_precision: Mapped[float]
    siren_code: Mapped[str]
    canton: Mapped[str]
    population: Mapped[int]
    multican: Mapped[str]
    cc_nom: Mapped[str]
    cc_siren: Mapped[int] = mapped_column(BigInteger)
    cc_nature: Mapped[str]
    cc_date_creation: Mapped[str]
    cc_date_effet: Mapped[str]
    insee_commune_nouvelle: Mapped[str]
    meta_create_date: Mapped[datetime]
    meta_update_date: Mapped[datetime]

    @hybrid_property
    def nom_com_dept(self):
        return f"{self.nom_com} ({self.insee_dep})"
