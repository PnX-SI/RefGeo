"""Add column LAreas.geom_4326

Revision ID: bc2fcc772b46
Revises: 795f6ea8ec45
Create Date: 2023-11-28 17:34:39.273235

"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision = "bc2fcc772b46"
down_revision = "795f6ea8ec45"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TRIGGER tri_calculate_geojson ON ref_geo.l_areas")
    op.execute("DROP FUNCTION ref_geo.fct_tri_calculate_geojson()")
    op.drop_column(
        schema="ref_geo",
        table_name="l_areas",
        column_name="geojson_4326",
    )
    op.add_column(
        schema="ref_geo",
        table_name="l_areas",
        column=sa.Column("geom_4326", Geometry("MULTIPOLYGON", 4326)),
    )
    op.execute(
        """
        CREATE FUNCTION ref_geo.fct_tri_transform_geom()
          RETURNS trigger AS
          $BODY$
            DECLARE
              local_srid integer;
              c integer;
            BEGIN
              IF (TG_OP = 'INSERT') THEN
                -- Insert policy: we set geom from geom_4326 if geom is null and geom_4326 is not null, and reciprocally.
                -- If both geom and geom_4326 have been set (or both are null), we do nothing.
                IF (NEW.geom IS NULL AND NEW.geom_4326 IS NOT NULL) THEN
                  NEW.geom = ST_Transform(NEW.geom_4326, local_srid);
                  RAISE NOTICE '(I) Updated geom';
                ELSEIF (NEW.geom IS NOT NULL AND NEW.geom_4326 IS NULL) THEN
                  NEW.geom_4326 = ST_Transform(NEW.geom, 4326);
                  RAISE NOTICE '(I) Updated geom_4326';
                END IF;
              ELSEIF (TG_OP = 'UPDATE') THEN
                -- Update policy: we set geom from geom_4326 if geom_4326 have been updated to non null value,
                -- unless geom have also been modified to non null value, and reciprocally.
                -- We also set geom from geom_4326 if geom is modified to null, and geom_4326 is not null (modified or not),
                -- in order to be consistent when updating one or two columns at the same time.
                IF (
                  NEW.geom_4326 IS NOT NULL
                  AND
                  (
                    (OLD.geom IS NOT DISTINCT FROM NEW.geom AND OLD.geom_4326 IS DISTINCT FROM NEW.geom_4326)
                    OR
                    (NEW.geom IS NULL AND OLD.geom IS NOT NULL)
                  )
                ) THEN
                  SELECT INTO local_srid Find_SRID('ref_geo', 'l_areas', 'geom');
                  NEW.geom = ST_Transform(NEW.geom_4326, local_srid);
                  RAISE NOTICE '(U) Updated geom';
                ELSEIF (
                  NEW.geom IS NOT NULL
                  AND
                  (
                    (OLD.geom_4326 IS NOT DISTINCT FROM NEW.geom_4326 AND OLD.geom IS DISTINCT FROM NEW.geom)
                    OR
                    (NEW.geom_4326 IS NULL AND OLD.geom_4326 IS NOT NULL)
                  )
                ) THEN
                  NEW.geom_4326 = ST_Transform(NEW.geom, 4326);
                  RAISE NOTICE '(U) Updated geom_4326';
                END IF;
              END IF;
              RETURN NEW;
            END;
          $BODY$
          LANGUAGE plpgsql VOLATILE
          COST 100;
        """
    )
    # Set geom_4326 before creating trigger!
    op.execute(
        """
        UPDATE
            ref_geo.l_areas
        SET
            geom_4326 = ST_Transform(geom, 4326)
        WHERE
            geom IS NOT NULL;
        """
    )
    op.execute(
        """
        CREATE TRIGGER tri_transform_geom_insert
            BEFORE
                INSERT ON ref_geo.l_areas
            FOR EACH
                ROW
            EXECUTE FUNCTION
                ref_geo.fct_tri_transform_geom();
        CREATE TRIGGER tri_transform_geom_update
            BEFORE
                UPDATE ON ref_geo.l_areas
            FOR EACH
                ROW
            EXECUTE FUNCTION
                ref_geo.fct_tri_transform_geom();
        """
    )


def downgrade():
    op.add_column(
        schema="ref_geo",
        table_name="l_areas",
        column=sa.Column("geojson_4326", sa.String),
    )
    op.execute(
        """
       UPDATE
           ref_geo.l_areas
       SET
           geojson_4326 = ST_AsGeoJson(geom_4326)
       """
    )
    op.execute("DROP TRIGGER tri_transform_geom_insert ON ref_geo.l_areas")
    op.execute("DROP TRIGGER tri_transform_geom_update ON ref_geo.l_areas")
    op.execute("DROP FUNCTION ref_geo.fct_tri_transform_geom()")
    op.drop_column(
        schema="ref_geo",
        table_name="l_areas",
        column_name="geom_4326",
    )
    op.execute(
        """
       CREATE OR REPLACE FUNCTION ref_geo.fct_tri_calculate_geojson()
          RETURNS trigger AS
         $BODY$
           BEGIN
             NEW.geojson_4326 = public.ST_asgeojson(public.st_transform(NEW.geom, 4326));
             RETURN NEW;
           END;
         $BODY$
         LANGUAGE plpgsql VOLATILE
         COST 100;
       """
    )
    op.execute(
        """
       CREATE TRIGGER tri_calculate_geojson
           BEFORE INSERT OR UPDATE OF geom ON ref_geo.l_areas
           FOR EACH ROW
           EXECUTE PROCEDURE ref_geo.fct_tri_calculate_geojson();
       """
    )
