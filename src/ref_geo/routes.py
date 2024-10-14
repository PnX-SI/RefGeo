from itertools import groupby
import json

from flask import Blueprint, request, current_app
from flask.json import jsonify
import sqlalchemy as sa
from sqlalchemy import func, select, asc, desc
from sqlalchemy.sql import text
from sqlalchemy.orm import joinedload, undefer, defer
from werkzeug.exceptions import BadRequest

from ref_geo.env import db
from ref_geo.models import BibAreasTypes, LiMunicipalities, LAreas
from ref_geo.schemas import AreaTypeSchema, MunicipalitySchema, AreaSchema


routes = Blueprint("ref_geo", __name__)


altitude_stmt = sa.select(sa.column("altitude_min"), sa.column("altitude_max")).select_from(
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

    areas = (
        select(LAreas)
        .filter_by(enable=True)
        .filter(geojson_intersect_filter.params(geojson=geojson))
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
                db.session.scalars(areas).unique().all(), many=True
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

    areas = (
        select(LAreas)
        .filter_by(enable=True)
        .filter(geojson_intersect_filter.params(geojson=geojson))
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
    for id_type, _areas in groupby(
        db.session.scalars(areas).unique().all(), key=lambda area: area.id_type
    ):
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

    q = select(LiMunicipalities).order_by(LiMunicipalities.nom_com.asc())

    if "nom_com" in parameters:
        search_name = request.args.get("nom_com")
        search_name = "%" + search_name.replace(" ", "%") + "%"
        q = q.where(func.unaccent(LiMunicipalities.nom_com).ilike(func.unaccent(search_name)))
    limit = int(parameters.get("limit")) if parameters.get("limit") else 100

    municipalities = db.session.scalars(q.limit(limit)).all()
    return jsonify(MunicipalitySchema().dump(municipalities, many=True))


# FIXME: Transform to post and change the post /areas
@routes.route("/areas", methods=["GET"])
def get_areas():
    """
    Return the areas of ref_geo.l_areas
    .. :quickref: Ref Geo;
    """
    # change all args in a list of value
    params = request.args

    # allow to format response
    output_format = request.args.get("format", default="", type=str)

    marsh_params = dict(as_geojson=(output_format == "geojson"))
    query = (
        select(LAreas)
        .options(joinedload("area_type").load_only("type_code"))
        .order_by(LAreas.area_name.asc())
    )

    if "enable" in params:
        enable_param = params["enable"].lower()
        accepted_enable_values = ["true", "false", "all"]
        if enable_param not in accepted_enable_values:
            response = {
                "message": f"Le paramètre 'enable' accepte seulement les valeurs: {', '.join(accepted_enable_values)}.",
                "status": "warning",
            }
            return response, 400
        if enable_param == "true":
            query = query.where(LAreas.enable == True)
        elif enable_param == "false":
            query = query.where(LAreas.enable == False)
    else:
        query = query.where(LAreas.enable == True)

    if "id_type" in params:
        # getlist() of request.args does not use the syntax url?param=val1,val2
        id_type = params.get("id_type").split(",")
        query = query.where(LAreas.id_type.in_(id_type))

    if "type_code" in params:
        # getlist() of request.args does not use the syntax url?param=val1,val2
        type_code = params.get("type_code").split(",")
        query = query.where(LAreas.area_type.has(BibAreasTypes.type_code.in_(type_code)))

    if "area_name" in params:
        search_name = request.args.get("area_name")
        search_name = "%" + search_name.replace(" ", "%") + "%"
        query = query.where(func.unaccent(LAreas.area_name).ilike(func.unaccent(search_name)))

    without_geom = request.args.get("without_geom", False, lambda x: x == "true")
    if without_geom:
        query = query.options(defer("geom"))
        marsh_params["exclude"] = ["geom"]

    limit = int(params.get("limit")) if params.get("limit") else 100

    fields = {"area_type.type_code"}
    if output_format == "geojson" and not without_geom:
        fields |= {"+geom_4326"}
        query = query.options(undefer("geom_4326"))

    areas = db.session.scalars(query.limit(limit)).unique().all()

    marsh_params["only"] = fields

    response = AreaSchema(**marsh_params).dump(areas, many=True)

    if output_format == "geojson":
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

    query = select(area_size_func.params(geojson=geojson))

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
    query = select(BibAreasTypes)
    # GET ONLY INFO FOR A SPECIFIC CODE
    if type_code:
        code_exists = db.session.execute(
            select(BibAreasTypes).where(BibAreasTypes.type_code == type_code)
        ).scalar_one_or_none()
        if not code_exists:
            raise BadRequest("This area type code does not exist")
        query = query.where(BibAreasTypes.type_code == type_code)
    # FILTER BY NAME
    if type_name:
        query = query.where(BibAreasTypes.type_name.ilike("%{}%".format(type_name)))
    # SORT
    if sort == "asc":
        query = query.order_by(asc("type_name"))
    if sort == "desc":
        query = query.order_by(desc("type_name"))
    # FIELDS
    fields = ["type_name", "type_code", "id_type"]
    return jsonify(AreaTypeSchema(only=fields).dump(db.session.scalars(query).all(), many=True))
