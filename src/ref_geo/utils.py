"""
methodes pour ref_geo
    - recupération du srid local
"""

from sqlalchemy import text


def get_local_srid(session):
    """
    permet de récupérer le srid local ( celui de ref_geo.l_areas.geom)
    """
    return session.execute(text("SELECT FIND_SRID('ref_geo', 'l_areas', 'geom')")).scalar()


def create_temporary_grids_table(conn, schema, temp_table_name):
    conn.execute(f"""
        CREATE TABLE {schema}.{temp_table_name} (
            gid integer NOT NULL,
            cd_sig character varying(21),
            code character varying(10),
            geom public.geometry(MultiPolygon,2154),
            geojson character varying
        )
    """)
    conn.execute(f"""
        ALTER TABLE ONLY {schema}.{temp_table_name}
            ADD CONSTRAINT {temp_table_name}_pkey PRIMARY KEY (gid)
    """)


def insert_areas_from_temporary_table(conn, schema, temp_table_name, area_type, enable=True):
    # We insert geom and geom_4326 to avoid double conversion like 2154 → 3312 → 4326
    conn.execute(f"""
        INSERT INTO {schema}.l_areas (id_type, area_code, area_name, geom, geom_4326, enable)
        SELECT
            {schema}.get_id_area_type('{area_type}') AS id_type,
            cd_sig,
            code,
            ST_Transform(geom, Find_SRID('{schema}', 'l_areas', 'geom')),
            ST_SetSRID(ST_GeomFromGeoJSON(geojson), 4326),
            {str(enable).upper()}
        FROM {schema}.{temp_table_name}
    """)
    conn.execute(f"REINDEX INDEX {schema}.index_l_areas_geom")


def insert_grids_from_temporary_table(conn, schema, temp_table_name):
    conn.execute(f"""
        INSERT INTO {schema}.li_grids(id_grid, id_area, cxmin, cxmax, cymin, cymax)
            SELECT
                l.area_code,
                l.id_area,
                ST_XMin(g.geom),
                ST_XMax(g.geom),
                ST_YMin(g.geom),
                ST_YMax(g.geom)
            FROM {schema}.{temp_table_name} g
            JOIN {schema}.l_areas l ON l.area_code = cd_sig;
    """)
