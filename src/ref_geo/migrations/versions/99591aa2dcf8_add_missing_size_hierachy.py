"""add missing size_hierachy (GRID 20)

Revision ID: 99591aa2dcf8
Revises: 10a587fb63d1
Create Date: 2025-05-21 10:55:43.345049

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "99591aa2dcf8"
down_revision = "10a587fb63d1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        update ref_geo.bib_areas_types 
        set size_hierarchy = 20000
        where type_code  = 'M20';
        """
    )


def downgrade():
    op.execute(
        """
        update ref_geo.bib_areas_types 
        set size_hierarchy = NULL
        where type_code  = 'M20';
        """
    )
