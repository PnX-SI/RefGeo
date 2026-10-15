from sqlalchemy import text

from ref_geo.env import db
from ref_geo.utils import get_local_srid


def expected_local_srid():
    return db.session.execute(text("""
            SELECT srid
            FROM public.geometry_columns
            WHERE f_table_schema = 'ref_geo'
                AND f_table_name = 'l_areas'
                AND f_geometry_column = 'geom'
            """)).scalar_one()


class TestUtils:
    def test_get_local_srid_with_connection(self):
        srid = get_local_srid(db.session.connection())
        assert isinstance(srid, int)
        assert srid == expected_local_srid()

    def test_get_local_srid_with_session(self):
        assert get_local_srid(db.session) == expected_local_srid()
