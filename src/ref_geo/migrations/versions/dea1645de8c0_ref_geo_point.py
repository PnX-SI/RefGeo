"""Référentiel point, cor (area, linear, point)

Revision ID: dea1645de8c0
Revises: f7374cd6e38d
Create Date: 2023-07-27 12:13:01.748452

"""

import importlib

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from ref_geo.utils import (
    get_local_srid,
)

# revision identifiers, used by Alembic.
revision = "dea1645de8c0"
down_revision = "f7374cd6e38d"
branch_labels = None
depends_on = None


def upgrade():
    stmt = text(importlib.resources.read_text("ref_geo.migrations.data", "ref_geo_point.sql"))
    op.get_bind().execute(stmt, {"local_srid": get_local_srid(op.get_bind())})

    pass


def downgrade():
    op.get_bind().execute(
        """
        DROP TABLE ref_geo.l_points;
        DROP TABLE ref_geo.bib_points_types;
    """
    )
    pass
