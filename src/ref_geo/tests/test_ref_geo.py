import pytest
import json

from flask import url_for, current_app
from flask_migrate import Migrate
from ref_geo.commands import change_area_activation_status
from werkzeug.exceptions import Unauthorized, BadRequest
from jsonschema import validate as validate_json
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

from ref_geo.env import db
from ref_geo.models import BibAreasTypes, LAreas
from sqlalchemy import select, update


polygon = {
    "type": "Polygon",
    "coordinates": [
        [
            [6.058788299560547, 44.740515073054915],
            [6.039562225341797, 44.7189291865304],
            [6.075954437255859, 44.70270398212803],
            [6.119728088378906, 44.70392408044993],
            [6.13861083984375, 44.73429623703402],
            [6.099643707275391, 44.75770484489134],
            [6.058788299560547, 44.740515073054915],
        ]
    ],
}

CITY = "La Motte-en-Champsaur"
PARAMETER_ENABLE = [
    (dict(area_code=["50120"]), "50120"),
    (dict(area_name=["Ain"]), "01"),
    (dict(area_type=["COM"]), "01005"),
    (
        dict(
            in_polygon="POLYGON ((-1.653442 49.628504, -1.588898 49.628504, -1.588898 49.653849, -1.653442 49.653849, -1.653442 49.628504))"
        ),
        "50129",
    ),
]


def has_french_dem():
    migrate = current_app.extensions["migrate"].migrate
    config = migrate.get_config()
    script = ScriptDirectory.from_config(config)
    migration_context = MigrationContext.configure(db.session.connection())
    current_heads = migration_context.get_current_heads()
    current_heads = set(map(lambda rev: rev.revision, script.get_all_current(current_heads)))
    return "1715cf31a75d" in current_heads  # ign bd alti


@pytest.fixture(scope="class")
def area_commune():
    return db.session.execute(select(BibAreasTypes).filter_by(type_code="COM")).scalar_one()


@pytest.fixture(scope="class")
def area_departement():
    return db.session.execute(select(BibAreasTypes).filter_by(type_code="DEP")).scalar_one()


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestRefGeo:
    expected_altitude = pytest.approx({"altitude_min": 984, "altitude_max": 2335}, rel=1e-2)
    expected_communes = {"La Motte-en-Champsaur", "Saint-Bonnet-en-Champsaur", "Aubessagne"}

    def test_get_geo_info(self):
        response = self.client.post(
            url_for("ref_geo.getGeoInfo"),
            json={
                "geometry": polygon,
                "area_type": "COM",
            },
        )
        assert response.status_code == 200
        communes = {area["area_name"] for area in response.json["areas"]}
        assert communes == self.expected_communes
        if not has_french_dem():
            pytest.xfail("No French DEM")
        assert response.json["altitude"] == self.expected_altitude

    def test_get_geo_no_payload(self):
        response = self.client.post(url_for("ref_geo.getGeoInfo"))

        assert response.status_code == 400
        assert response.json["description"] == "Missing request payload"

    def test_get_geo_no_geom(self):
        response = self.client.post(url_for("ref_geo.getGeoInfo"), json={})

        assert response.status_code == 400
        assert response.json["description"] == "Missing 'geometry' in request payload"

    def test_get_geo_info_id_type_error(self):
        response = self.client.post(
            url_for("ref_geo.getGeoInfo"),
            json={
                "geometry": polygon,
                "id_type": "aWrongType",
            },
        )

        assert response.status_code == 400
        assert response.json["description"] == "Parameter 'id_type' must be an integer"

    def test_get_geo_info_id_type(self, area_commune):
        id_type = area_commune.id_type

        response = self.client.post(
            url_for("ref_geo.getGeoInfo"),
            json={
                "geometry": polygon,
                "id_type": int(id_type),
            },
        )

        assert all(area["id_type"] == id_type for area in response.json["areas"])

    def test_get_altitude(self):
        if not has_french_dem():
            pytest.xfail("No French DEM")
        response = self.client.post(
            url_for("ref_geo.getAltitude"),
            json={
                "geometry": polygon,
            },
        )
        assert response.status_code == 200
        assert response.json == self.expected_altitude

    def test_get_altitude_no_payload(self):
        if not has_french_dem():
            pytest.xfail("No French DEM")

        response = self.client.post(url_for("ref_geo.getAltitude"))

        assert response.status_code == 400
        assert response.json["description"] == "Missing request payload"

    def test_get_altitude_no_geometry(self):
        if not has_french_dem():
            pytest.xfail("No French DEM")

        response = self.client.post(url_for("ref_geo.getAltitude"), json={})

        assert response.status_code == 400
        assert response.json["description"] == "Missing 'geometry' in request payload"

    def test_get_area_intersection(self, area_commune):
        response = self.client.post(
            url_for("ref_geo.getAreasIntersection"),
            json={
                "geometry": polygon,
            },
        )
        assert response.status_code == 200
        validate_json(
            instance=response.json,
            schema={
                "type": "object",
                "patternProperties": {
                    "[0-9]*": {
                        "type": "object",
                        "properties": {
                            "type_code": {
                                "type": "string",
                            },
                            "type_name": {
                                "type": "string",
                            },
                            "areas": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "area_code": {
                                            "type": "string",
                                        },
                                        "area_name": {
                                            "type": "string",
                                        },
                                        "id_area": {
                                            "type": "integer",
                                        },
                                        "id_type": {
                                            "type": "integer",
                                        },
                                    },
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "additionalProperties": False,
                    },
                },
                "additionalProperties": False,
            },
        )

        communes = {
            area["area_name"] for area in response.json[str(area_commune.id_type)]["areas"]
        }
        assert communes == self.expected_communes

    def test_get_area_intersection_no_payload(self):
        response = self.client.post(url_for("ref_geo.getAreasIntersection"))

        assert response.status_code == 400
        assert response.json["description"] == "Missing request payload"

    def test_get_area_intersection_no_geom(self):
        response = self.client.post(url_for("ref_geo.getAreasIntersection"), json={})

        assert response.status_code == 400
        assert response.json["description"] == "Missing 'geometry' in request payload"

    def test_get_area_intersection_id_type(self, area_commune):
        id_type = area_commune.id_type

        response = self.client.post(
            url_for("ref_geo.getAreasIntersection"), json={"geometry": polygon, "id_type": id_type}
        )
        assert response.status_code == 200
        resp_json = response.json
        for area_type in resp_json.values():
            for area in area_type["areas"]:
                assert area["id_type"] == id_type

    def test_get_area_intersection_id_type_wrong(self):
        response = self.client.post(
            url_for("ref_geo.getAreasIntersection"),
            json={"geometry": polygon, "id_type": "wrongType"},
        )
        assert response.status_code == 400
        assert response.json["description"] == "Parameter 'id_type' must be an integer"

    def test_get_area_intersection_area_type(self, area_commune):
        area_type = area_commune.type_code

        response = self.client.post(
            url_for("ref_geo.getAreasIntersection"),
            json={"geometry": polygon, "area_type": area_type},
        )

        assert response.status_code == 200
        resp_json = response.json
        assert all(a_type["type_code"] == area_type for a_type in resp_json.values())

    def test_get_municipalities(self):
        response = self.client.get(url_for("ref_geo.get_municipalities"))
        assert response.status_code == 200

    def test_get_municipalities_nom_com(self):
        response = self.client.get(
            url_for("ref_geo.get_municipalities"), query_string={"nom_com": CITY}
        )

        assert response.status_code == 200
        assert response.json[0]["nom_com"] == CITY

    def test_get_areas(self):
        response = self.client.get(url_for("ref_geo.get_areas"))
        assert response.status_code == 200

    def test_get_areas_enable_wrong(self):
        response = self.client.get(url_for("ref_geo.get_areas"), query_string={"enable": "wrong"})

        assert response.status_code == 400
        assert (
            response.json["message"]
            == "Le paramètre 'enable' accepte seulement les valeurs: true, false, all."
        )

    def test_get_areas_enable_false(self):
        response = self.client.get(url_for("ref_geo.get_areas"), query_string={"enable": False})

        assert response.status_code == 200
        assert all(not area["enable"] for area in response.json)

    def test_get_areas_enable_true(self):
        response = self.client.get(url_for("ref_geo.get_areas"), query_string={"enable": True})

        assert response.status_code == 200
        assert all(area["enable"] for area in response.json)

    def test_get_areas_id_type(self, area_commune):
        id_type_commune = area_commune.id_type

        response = self.client.get(
            url_for("ref_geo.get_areas"), query_string={"id_type": id_type_commune}
        )

        assert response.status_code == 200
        assert all(area["id_type"] == id_type_commune for area in response.json)

    def test_get_areas_type_code(self, area_commune):
        type_code = area_commune.type_code

        response = self.client.get(
            url_for("ref_geo.get_areas"), query_string={"type_code": type_code}
        )

        assert response.status_code == 200
        assert all(area["id_type"] == area_commune.id_type for area in response.json)

    def test_get_areas_type_codes(self, area_commune, area_departement):

        type_codes = [area_commune.type_code, area_departement.type_code]

        response = self.client.get(
            url_for("ref_geo.get_areas"), query_string={"type_code": ",".join(type_codes)}
        )

        assert response.status_code == 200
        assert all(
            area["id_type"] in [area_commune.id_type, area_departement.id_type]
            for area in response.json
        )

    def test_get_areas_area_name(self):
        response = self.client.get(url_for("ref_geo.get_areas"), query_string={"area_name": CITY})

        assert response.status_code == 200
        assert response.json[0]["area_name"] == CITY

    def test_get_without_geom(self):
        response = self.client.get(
            url_for("ref_geo.get_areas"), query_string={"without_geom": "false"}
        )
        assert response.status_code == 200
        for area in response.json:
            assert "geom" in area

        response = self.client.get(
            url_for("ref_geo.get_areas"), query_string={"without_geom": "true"}
        )
        assert response.status_code == 200
        for area in response.json:
            assert not "geom" in area

    def test_get_areas_as_geojson(self, area_commune):
        """
        This test can't try to get only one commune
        Example : if first commune is Aast, we can get many result with ilike operator
        """
        type_code = area_commune.type_code
        id_type = area_commune.id_type
        first_comm = db.session.scalars(db.select(LAreas).where(LAreas.id_type == id_type)).first()
        # will test many responses are return
        response = self.client.get(
            url_for("ref_geo.get_areas"),
            query_string={"type_code": type_code, "format": "geojson"},
        )
        assert response.status_code == 200
        assert len(response.json) > 0
        result_comm = response.json[0]
        result_type = result_comm["properties"]["area_type"]["type_code"]
        assert result_comm["geometry"] is not None
        assert result_type == type_code
        # will test only one response with correct format
        response = self.client.get(
            url_for("ref_geo.get_areas"),
            query_string={
                "type_code": type_code,
                "format": "geojson",
                "area_name": first_comm.area_name,
            },
        )
        result = response.json[0]
        assert result["geometry"] is not None
        assert result["properties"]["id_type"] == first_comm.id_type

    def test_get_area_size(self):
        response = self.client.post(
            url_for("ref_geo.get_area_size"),
            json={
                "geometry": polygon,
            },
        )
        assert response.status_code == 200
        assert response.json == pytest.approx(30526916, rel=1e-3)

    def test_get_area_size_no_payload(self):
        response = self.client.post(url_for("ref_geo.get_area_size"))

        assert response.status_code == 400
        assert response.json["description"] == "Missing request payload"

    def test_get_area_size_no_geom(self):
        response = self.client.post(url_for("ref_geo.get_area_size"), json={})

        assert response.status_code == 400
        assert response.json["description"] == "Missing 'geometry' in request payload"

    def test_get_types(self):
        response = self.client.get(url_for("ref_geo.get_area_types"))
        assert response.status_code == 200

    def test_get_types_by_code(self, area_commune):
        type_code = area_commune.type_code

        # GET area type with fake code
        response = self.client.get(
            url_for("ref_geo.get_area_types"), query_string={"code": type_code + "_FOO"}
        )
        assert response.status_code == BadRequest.code

        # GET area type with correct code
        response = self.client.get(
            url_for("ref_geo.get_area_types"), query_string={"code": type_code}
        )
        area = response.json[0]
        assert response.status_code == 200
        assert area["type_name"] == area_commune.type_name
        assert area["type_code"] == area_commune.type_code
        assert area["id_type"] == area_commune.id_type

    def test_get_types_by_name(self, area_commune):
        type_name = area_commune.type_name
        # GET area type with correct name
        response = self.client.get(
            url_for("ref_geo.get_area_types"), query_string={"name": area_commune.type_name}
        )
        assert response.status_code == 200
        assert response.json[0]["type_code"] == area_commune.type_code

        # GET area type with fake name
        response = self.client.get(
            url_for("ref_geo.get_area_types"), query_string={"name": type_name + "_FOO"}
        )
        assert response.status_code == 200
        assert len(response.json) == 0

        # GET area type with exact name
        response = self.client.get(
            url_for("ref_geo.get_area_types"), query_string={"name": type_name}
        )
        assert response.status_code == 200
        assert response.json[0]["type_code"] == area_commune.type_code

        # GET area type with part of name
        response = self.client.get(
            url_for("ref_geo.get_area_types"), query_string={"name": type_name[:1]}
        )
        assert response.status_code == 200
        assert len(response.json) > 0

    @pytest.mark.parametrize(
        "parameters,expected_area_code",
        PARAMETER_ENABLE,
    )
    def test_activate_areas(self, parameters, expected_area_code):
        db.session.execute(
            update(LAreas).where(LAreas.area_code == expected_area_code).values(enable=False)
        )
        change_area_activation_status(**parameters, enable=True)
        q = select(LAreas.enable).where(LAreas.area_code == expected_area_code)
        assert db.session.scalar(q) == True

    @pytest.mark.parametrize(
        "parameters,expected_area_code",
        PARAMETER_ENABLE,
    )
    def test_deactivate_areas(self, parameters, expected_area_code):
        db.session.execute(
            update(LAreas).where(LAreas.area_code == expected_area_code).values(enable=True)
        )
        change_area_activation_status(**parameters, enable=False)
        q = select(LAreas.enable).where(LAreas.area_code == expected_area_code)
        assert db.session.scalar(q) == False
