"""Rewrite function ref_geo.fct_get_altitude_intersection

Revision ID: 1fdac7036dd9
Revises: f7374cd6e38d
Create Date: 2023-04-20 11:45:44.896318

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1fdac7036dd9"
down_revision = "f22d70b8fcfa"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION ref_geo.fct_get_altitude_intersection(
            mygeom geometry
        )
            RETURNS TABLE(altitude_min integer, altitude_max integer)
            LANGUAGE 'plpgsql'
            COST 100
            IMMUTABLE PARALLEL UNSAFE
            ROWS 1000
        AS $BODY$
            DECLARE
                thesrid int;
                is_vectorized int;
            BEGIN
              SELECT Find_SRID('ref_geo', 'l_areas', 'geom')
              INTO thesrid;

              SELECT COALESCE(gid, NULL)
              FROM ref_geo.dem_vector
              LIMIT 1
              INTO is_vectorized;

            IF is_vectorized IS NULL AND st_geometrytype(myGeom) = 'ST_Point' THEN
               -- Use dem and st_value function
                RETURN QUERY WITH alt AS (
                    SELECT st_value(rast, public.st_transform(myGeom, thesrid))::int altitude
                    FROM ref_geo.dem AS altitude
                    WHERE public.st_intersects(rast, public.st_transform(myGeom, thesrid))
                )
                SELECT min(altitude) AS altitude_min, max(altitude) AS altitude_max
                FROM alt;
            ELSIF is_vectorized IS NULL THEN
                -- Use dem ans st_intersection function
                RETURN QUERY
                SELECT min((altitude).val)::integer AS altitude_min, max((altitude).val)::integer AS altitude_max
                FROM (
                    SELECT public.ST_Intersection(
                        rast,
                        public.ST_Transform(myGeom, thesrid)
                    ) AS altitude
                    FROM ref_geo.dem AS altitude
                    WHERE public.ST_Intersects(rast,public.ST_Transform(myGeom, thesrid))
                ) AS a;
              -- Use dem_vector
            ELSE
                RETURN QUERY
                WITH d AS (
                    SELECT public.ST_Transform(myGeom,thesrid) a
                 )
                SELECT min(val)::int AS altitude_min, max(val)::int AS altitude_max
                FROM ref_geo.dem_vector, d
                WHERE public.ST_Intersects(a,geom);
              END IF;
            END;

        $BODY$;
        """
    )


def downgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION ref_geo.fct_get_altitude_intersection(
            mygeom geometry
        )
            RETURNS TABLE(altitude_min integer, altitude_max integer)
            LANGUAGE 'plpgsql'
            COST 100
            VOLATILE PARALLEL UNSAFE
            ROWS 1000

        AS $BODY$
            DECLARE
                thesrid int;
                is_vectorized int;
            BEGIN
                SELECT Find_SRID('ref_geo', 'l_areas', 'geom')
                INTO thesrid;

                SELECT COALESCE(gid, NULL)
                FROM ref_geo.dem_vector
                LIMIT 1
                INTO is_vectorized;

                IF is_vectorized IS NULL THEN
                -- Use dem
                    RETURN QUERY
                        SELECT min((altitude).val)::integer AS altitude_min, max((altitude).val)::integer AS altitude_max
                        FROM (
                            SELECT public.ST_DumpAsPolygons(public.ST_Clip(
                                rast,
                                1,
                                public.ST_Transform(myGeom,thesrid),
                                true)
                            ) AS altitude
                            FROM ref_geo.dem AS altitude
                            WHERE public.ST_Intersects(rast, public.ST_Transform(myGeom, thesrid))
                        ) AS a;
                -- Use dem_vector
                ELSE
                    RETURN QUERY
                        WITH d  as (
                            SELECT public.ST_Transform(myGeom,thesrid) a
                         )
                        SELECT min(val)::int as altitude_min, max(val)::int as altitude_max
                        FROM ref_geo.dem_vector, d
                        WHERE public.ST_Intersects(a,geom);
                END IF;
            END;

        $BODY$;
        """
    )
