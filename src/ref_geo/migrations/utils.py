from alembic import op, context
import sqlalchemy as sa
import logging
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from shutil import copyfileobj
from urllib.request import urlopen
import lzma
import os, os.path

from utils_flask_sqla.migrations.utils import logger


schema = "ref_geo"


def geom_4326_exists():
    return (
        op.get_bind()
        .execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.COLUMNS
                WHERE table_schema = 'ref_geo' AND table_name='l_areas' AND column_name = 'geom_4326'
            )
            """
        )
        .scalar()
    )


def delete_area_with_type(area_type):
    """
    Supprimer les zones d’un type donnée, e.g. 'DEP', 'COM', …
    """
    op.execute(
        f"""
        DELETE FROM {schema}.l_areas la
        USING {schema}.get_id_area_type('{area_type}') as area_type
        WHERE la.id_type = area_type
    """
    )


def create_temporary_grids_table(schema, temp_table_name):
    logger.info("Create temporary grids table…")
    op.execute(
        f"""
        CREATE TABLE {schema}.{temp_table_name} (
            gid integer NOT NULL,
            cd_sig character varying(21),
            code character varying(10),
            geom public.geometry(MultiPolygon,2154),
            geojson character varying
        )
    """
    )
    op.execute(
        f"""
        ALTER TABLE ONLY {schema}.{temp_table_name}
            ADD CONSTRAINT {temp_table_name}_pkey PRIMARY KEY (gid)
    """
    )


def insert_grids_and_drop_temporary_table(schema, temp_table_name, area_type):
    logger.info("Copy grids in l_areas…")
    if geom_4326_exists():
        # We insert geom and geom_4326 to avoid double conversion like 2154 → 3312 → 4326
        op.execute(
            f"""
            INSERT INTO {schema}.l_areas (id_type, area_code, area_name, geom, geom_4326)
            SELECT
                {schema}.get_id_area_type('{area_type}') AS id_type,
                cd_sig,
                code,
                ST_Transform(geom, Find_SRID('{schema}', 'l_areas', 'geom')),
                ST_SetSRID(ST_GeomFromGeoJSON(geojson), 4326)
            FROM {schema}.{temp_table_name}
        """
        )
    else:  # legacy column geojson_4326
        op.execute(
            f"""
            INSERT INTO {schema}.l_areas (id_type, area_code, area_name, geom, geojson_4326)
            SELECT
                {schema}.get_id_area_type('{area_type}') AS id_type,
                cd_sig,
                code,
                ST_Transform(geom, Find_SRID('{schema}', 'l_areas', 'geom')),
                geojson
            FROM {schema}.{temp_table_name}
        """
        )
    logger.info("Copy grids in li_grids…")
    op.execute(
        f"""
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
    """
    )
    logger.info("Re-indexing…")
    op.execute(f"REINDEX INDEX {schema}.index_l_areas_geom")
    logger.info("Dropping temporary grids table…")
    op.execute(f"DROP TABLE {schema}.{temp_table_name}")
