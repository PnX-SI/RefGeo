"""Insert INPN 50×50 grids in ref_geo

Revision ID: 4d0c35ea0cfe
Create Date: 2024-04-23 16:15:26.220548

"""

from alembic import op

from utils_flask_sqla.migrations.utils import logger, open_remote_file
from ref_geo.migrations.utils import (
    schema,
    create_temporary_grids_table,
    delete_area_with_type,
    insert_grids_and_drop_temporary_table,
)


# revision identifiers, used by Alembic.
revision = "4d0c35ea0cfe"
down_revision = None
branch_labels = ("ref_geo_inpn_grids_50",)
depends_on = "6afe74833ed0"

grid = "50"
filename = f"inpn_grids_{grid}.csv.xz"
base_url = "http://geonature.fr/data/inpn/layers/2024/"
temp_table_name = f"temp_grids_{grid}"
area_type = f"M{grid}"


def upgrade():
    op.execute(
        f"""
INSERT INTO {schema}.bib_areas_types (type_name,
                                     type_code,
                                     type_desc,
                                     ref_name,
                                     ref_version,
                                     num_version)
VALUES ('Mailles {grid}*{grid}', 'M{grid}', 'Type maille INPN {grid}*{grid}km', NULL, NULL, NULL)
ON CONFLICT (type_code) DO NOTHING;
    """
    )
    create_temporary_grids_table(schema, temp_table_name)
    cursor = op.get_bind().connection.cursor()
    with open_remote_file(base_url, filename) as geofile:
        logger.info("Inserting grids data in temporary table…")
        cursor.copy_expert(f"COPY {schema}.{temp_table_name} FROM STDIN", geofile)
    insert_grids_and_drop_temporary_table(schema, temp_table_name, area_type)


def downgrade():
    delete_area_with_type(area_type)
