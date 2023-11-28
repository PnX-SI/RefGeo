from itertools import groupby
import json

from flask import Blueprint, request, current_app
from flask.json import jsonify
import sqlalchemy as sa
from sqlalchemy import func, distinct, asc, desc
from sqlalchemy.sql import text
from sqlalchemy.orm import joinedload, undefer
from werkzeug.exceptions import BadRequest

from ref_geo.env import db
from ref_geo.models import BibAreasTypes, LiMunicipalities, LAreas
from ref_geo.schemas import AreaTypeSchema, MunicipalitySchema, AreaSchema


routes = Blueprint("ref_geo", __name__)


altitude_stmt = sa.select(
    [
        sa.column("altitude_min"),
        sa.column("altitude_max"),
    ]
).select_from(
    func.ref_geo.fct_get_altitude_intersection(
        func.ST_SetSRID(
            func.ST_GeomFromGeoJSON(sa.bindparam("geojson")),
            4326,
        ),
    )
)

geojson_intersect_filter = func.ST_Intersects(
    LAreas.geom_4326,
    func.ST_SetSRID(func.ST_GeomFromGeoJSON(sa.bindparam("geojson")), 4326),
)

area_size_func = func.ST_Area(
    func.ST_Transform(
        func.ST_SetSrid(
            func.ST_GeomFromGeoJSON(sa.bindparam("geojson")),
            4326,
        ),
        func.Find_SRID("ref_geo", "l_areas", "geom"),
    )
)


@routes.route("/info", methods=["POST"])
def getGeoInfo():
    """
    From a posted geojson, the route return the municipalities intersected
    and the altitude min/max

    .. :quickref: Ref Geo;
    """
    if not request.is_json or request.json is None:
        raise BadRequest("Missing request payload")
    try:
        geojson = request.json["geometry"]
    except KeyError:
        raise BadRequest("Missing 'geometry' in request payload")
    geojson = json.dumps(geojson)

    areas = LAreas.query.filter_by(enable=True).filter(
        geojson_intersect_filter.params(geojson=geojson)
    )
    if "area_type" in request.json:
        areas = areas.join(BibAreasTypes).filter_by(type_code=request.json["area_type"])
    elif "id_type" in request.json:
        try:
            id_type = int(request.json["id_type"])
        except ValueError:
            raise BadRequest("Parameter 'id_type' must be an integer")
        areas = areas.filter_by(id_type=id_type)

    altitude = dict(db.session.execute(altitude_stmt, params={"geojson": geojson}).fetchone())

    return jsonify(
        {
            "areas": AreaSchema(only=["id_area", "id_type", "area_code", "area_name"]).dump(
                areas.all(), many=True
            ),
            "altitude": altitude,
        }
    )


@routes.route("/altitude", methods=["POST"])
def getAltitude():
    """
    From a posted geojson get the altitude min/max

    .. :quickref: Ref Geo;
    """
    if not request.is_json:
        raise BadRequest("Missing request payload")
    try:
        geojson = request.json["geometry"]
    except KeyError:
        raise BadRequest("Missing 'geometry' in request payload")
    geojson = json.dumps(geojson)

    altitude = db.session.execute(altitude_stmt, params={"geojson": geojson}).fetchone()
    return jsonify(altitude)


@routes.route("/areas", methods=["POST"])
def getAreasIntersection():
    """
    From a posted geojson, the route return all the area intersected
    from l_areas
    .. :quickref: Ref Geo;
    """
    if not request.is_json or request.json is None:
        raise BadRequest("Missing request payload")
    try:
        geojson = request.json["geometry"]
    except KeyError:
        raise BadRequest("Missing 'geometry' in request payload")
    geojson = json.dumps(geojson)

    areas = LAreas.query.filter_by(enable=True).filter(
        geojson_intersect_filter.params(geojson=geojson)
    )
    if "area_type" in request.json:
        areas = areas.join(BibAreasTypes).filter_by(type_code=request.json["area_type"])
    elif "id_type" in request.json:
        try:
            id_type = int(request.json["id_type"])
        except ValueError:
            raise BadRequest("Parameter 'id_type' must be an integer")
        areas = areas.filter_by(id_type=id_type)
    areas = areas.order_by(LAreas.id_type)

    response = {}
    for id_type, _areas in groupby(areas.all(), key=lambda area: area.id_type):
        _areas = list(_areas)
        response[id_type] = _areas[0].area_type.as_dict(fields=["type_code", "type_name"])
        response[id_type].update(
            {
                "areas": AreaSchema(
                    only=[
                        "area_code",
                        "area_name",
                        "id_area",
                        "id_type",
                    ]
                ).dump(_areas, many=True)
            }
        )

    return jsonify(response)


@routes.route("/municipalities", methods=["GET"])
def get_municipalities():
    """
    Return the municipalities
    .. :quickref: Ref Geo;
    """
    parameters = request.args

    q = db.session.query(LiMunicipalities).order_by(LiMunicipalities.nom_com.asc())

    if "nom_com" in parameters:
        q = q.filter(LiMunicipalities.nom_com.ilike("{}%".format(parameters.get("nom_com"))))
    limit = int(parameters.get("limit")) if parameters.get("limit") else 100

    municipalities = q.limit(limit)
    return jsonify(MunicipalitySchema().dump(municipalities, many=True))


@routes.route("/areas", methods=["GET"])
def get_areas():
    """
    Return the areas of ref_geo.l_areas
    .. :quickref: Ref Geo;
    """
    # change all args in a list of value
    params = {key: request.args.getlist(key) for key, value in request.args.items()}

    q = (
        db.session.query(LAreas)
        .options(joinedload("area_type").load_only("type_code"))
        .order_by(LAreas.area_name.asc())
    )

    if "enable" in params:
        enable_param = params["enable"][0].lower()
        accepted_enable_values = ["true", "false", "all"]
        if enable_param not in accepted_enable_values:
            response = {
                "message": f"Le paramètre 'enable' accepte seulement les valeurs: {', '.join(accepted_enable_values)}.",
                "status": "warning",
            }
            return response, 400
        if enable_param == "true":
            q = q.filter(LAreas.enable == True)
        elif enable_param == "false":
            q = q.filter(LAreas.enable == False)
    else:
        q = q.filter(LAreas.enable == True)

    if "id_type" in params:
        q = q.filter(LAreas.id_type.in_(params["id_type"]))

    if "type_code" in params:
        q = q.filter(LAreas.area_type.has(BibAreasTypes.type_code.in_(params["type_code"])))

    if "area_name" in params:
        q = q.filter(LAreas.area_name.ilike("%{}%".format(params.get("area_name")[0])))

    limit = int(params.get("limit")[0]) if params.get("limit") else 100

    areas = q.limit(limit)

    # allow to format response
    format = request.args.get("format", default="", type=str)

    fields = {"area_type.type_code"}
    if format == "geojson":
        fields |= {"+geom_4326"}
        areas = areas.options(undefer("geom_4326"))
    response = AreaSchema(only=fields, as_geojson=format == "geojson").dump(areas.all(), many=True)
    if format == "geojson":
        # retro-compat: return a list of Features instead of the FeatureCollection
        response = response["features"]
    return response


@routes.route("/area_size", methods=["Post"])
def get_area_size():
    """
    Return the area size from a given geojson

    .. :quickref: Ref Geo;

    :returns: An area size (int)
    """
    if not request.is_json or request.json is None:
        raise BadRequest("Missing request payload")
    try:
        geojson = request.json["geometry"]
    except KeyError:
        raise BadRequest("Missing 'geometry' in request payload")
    geojson = json.dumps(geojson)

    query = db.session.query(area_size_func.params(geojson=geojson))

    return jsonify(db.session.execute(query).scalar())


@routes.route("/types", methods=["Get"])
def get_area_types():
    """
    Get areas types list

    .. :quickref: Areas;

    :query str code: Type area code (ref_geo.bib_areas_types.type_code)
    :query str name: Type area name (ref_geo.bib_areas_types.type_name)
    :query str sort: sort value as ASC - DESC
    """
    type_code = request.args.get("code")
    type_name = request.args.get("name")
    sort = request.args.get("sort")
    query = db.session.query(BibAreasTypes)
    # GET ONLY INFO FOR A SPECIFIC CODE
    if type_code:
        code_exists = (
            db.session.query(BibAreasTypes)
            .filter(BibAreasTypes.type_code == type_code)
            .one_or_none()
        )
        if not code_exists:
            raise BadRequest("This area type code does not exist")
        query = query.filter(BibAreasTypes.type_code == type_code)
    # FILTER BY NAME
    if type_name:
        query = query.filter(BibAreasTypes.type_name.ilike("%{}%".format(type_name)))
    # SORT
    if sort == "asc":
        query = query.order_by(asc("type_name"))
    if sort == "desc":
        query = query.order_by(desc("type_name"))
    # FIELDS
    fields = ["type_name", "type_code", "id_type"]
    return jsonify(AreaTypeSchema(only=fields).dump(query.all(), many=True))
