from marshmallow_sqlalchemy.fields import Nested

from utils_flask_sqla.schema import SmartRelationshipsMixin
from utils_flask_sqla_geo.schema import GeoAlchemyAutoSchema

from ref_geo.env import db, ma
from ref_geo.models import BibAreasTypes, LAreas, LiMunicipalities


class AreaTypeSchema(SmartRelationshipsMixin, ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BibAreasTypes
        include_fk = True
        load_instance = True


class AreaSchema(SmartRelationshipsMixin, GeoAlchemyAutoSchema):
    class Meta:
        model = LAreas
        include_fk = True
        load_instance = True
        feature_geometry = "geom_4326"

    area_type = Nested(AreaTypeSchema)


class MunicipalitySchema(SmartRelationshipsMixin, GeoAlchemyAutoSchema):
    class Meta:
        model = LiMunicipalities
        include_fk = True
        load_instance = True
