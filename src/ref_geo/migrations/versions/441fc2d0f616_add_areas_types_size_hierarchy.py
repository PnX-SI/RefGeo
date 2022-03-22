"""add areas types size hierarchy

Revision ID: 441fc2d0f616
Revises: 681306b27407
Create Date: 2022-03-22 15:47:18.775255

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '441fc2d0f616'
down_revision = '681306b27407'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE ref_geo.bib_areas_types
        ADD COLUMN size_hierarchy INT default NULL;

    COMMENT ON COLUMN ref_geo.bib_areas_types.size_hierarchy IS
        'Diamètre moyen en mètres de ce type zone. Permet d''établir une hiérarchie des types '
        'de zone géographique. Utile pour le floutage des observations.' ;
    """)

    op.execute("""
    UPDATE ref_geo.bib_areas_types SET size_hierarchy = 200000 WHERE type_code = 'REG' ;
    UPDATE ref_geo.bib_areas_types SET size_hierarchy = 75000 WHERE type_code = 'DEP' ;
    UPDATE ref_geo.bib_areas_types SET size_hierarchy = 5000 WHERE type_code = 'COM' ;
    UPDATE ref_geo.bib_areas_types SET size_hierarchy = 10000 WHERE type_code = 'M10' ;
    UPDATE ref_geo.bib_areas_types SET size_hierarchy = 5000 WHERE type_code = 'M5' ;
    UPDATE ref_geo.bib_areas_types SET size_hierarchy = 1000 WHERE type_code = 'M1' ;
    """)


def downgrade():
    op.execute("""
    ALTER TABLE ref_geo.bib_areas_types
        DROP COLUMN size_hierarchy;
    """)

