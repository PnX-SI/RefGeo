"""add missing size_hierachy

Revision ID: e58071a29130
Revises: 4d0c35ea0cfe
Create Date: 2025-05-21 10:54:32.206749

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e58071a29130"
down_revision = "4d0c35ea0cfe"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    update ref_geo.bib_areas_types 
    set size_hierarchy = 50000
    where type_code  = 'M50';
    """
    )


def downgrade():
    op.execute(
        """
        update ref_geo.bib_areas_types 
        set size_hierarchy = NULL
        where type_code  = 'M50';
        """
    )
