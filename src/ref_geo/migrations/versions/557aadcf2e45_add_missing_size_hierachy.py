"""add missing size_hierachy (Grid 2)

Revision ID: 557aadcf2e45
Revises: 175cdb17343f
Create Date: 2025-05-21 10:55:50.994117

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "557aadcf2e45"
down_revision = "175cdb17343f"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        update ref_geo.bib_areas_types 
        set size_hierarchy = 2000
        where type_code  = 'M2';
        """
    )


def downgrade():
    op.execute(
        """
        update ref_geo.bib_areas_types 
        set size_hierarchy = NULL
        where type_code  = 'M2';
        """
    )
