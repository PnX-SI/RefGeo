"""empty message

Revision ID: fda887e7b578
Revises: 0dfdbfbccd63
Create Date: 2023-02-28 13:25:40.908589

"""

from alembic import op
from utils_flask_sqla.migrations.utils import logger


# revision identifiers, used by Alembic.
revision = "fda887e7b578"
down_revision = "0dfdbfbccd63"
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Correct area_name for communes (for characters Œ and œ)")
    op.execute(
        f"""
        update ref_geo.l_areas
            set area_name = replace(area_name, '¼', 'Œ')
            where area_name like '%¼%';
        update ref_geo.l_areas
            set area_name = replace(area_name, '½', 'œ')
            where area_name like '%½%';
"""
    )


def downgrade():
    op.execute(
        f"""
        update ref_geo.l_areas
            set area_name = replace(area_name, 'Œ', '¼')
            where area_name like '%Œ%';
        update ref_geo.l_areas
            set area_name = replace(area_name, 'œ', '½')
            where area_name like '%œ%';
"""
    )
