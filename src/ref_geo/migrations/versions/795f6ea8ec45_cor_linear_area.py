"""cor_areas & cor_linear_areas

Revision ID: 795f6ea8ec45
Revises: dea1645de8c0
Create Date: 2023-08-02 11:48:06.329936

"""

import sqlalchemy as sa
import importlib

from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = "795f6ea8ec45"
down_revision = "dea1645de8c0"
branch_labels = None
depends_on = None


def upgrade():
    stmt = text(importlib.resources.read_text("ref_geo.migrations.data", "ref_geo_cor.sql"))
    op.get_bind().execute(stmt)


def downgrade():
    op.get_bind().execute(
        """
        DROP TABLE ref_geo.cor_linear_area;
        DROP TABLE ref_geo.cor_areas;
    """
    )

    pass
