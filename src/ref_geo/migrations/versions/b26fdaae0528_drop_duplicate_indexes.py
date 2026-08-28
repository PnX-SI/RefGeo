"""Drop duplicate indexes.

Revision ID: b26fdaae0528
Revises: 1ca7fd0d2ea
Create Date: 2025-06-16 17:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b26fdaae0528"
down_revision = "1ca7fd0d2ea"
branch_labels = None
depends_on = None


def upgrade():
    """Drops some unique indexes
    redundants with unique constraints on the same columns.
    """

    # redundant with unique_id_type_area_code
    op.drop_index(
        "i_unique_l_areas_id_type_area_code",
        schema="ref_geo",
        table_name="l_areas",
        if_exists=True,
    )

    # redundant with unique_bib_areas_types_type_code
    op.drop_index(
        "i_unique_bib_areas_types_type_code",
        schema="ref_geo",
        table_name="bib_area_types",
        if_exists=True,
    )


def downgrade():
    """Creates back the redundant indexes."""

    op.create_index(
        "i_unique_l_areas_id_type_area_code",
        schema="ref_geo",
        table_name="l_areas",
        columns=["id_type", "area_code"],
        unique=True,
    )

    op.create_index(
        "i_unique_bib_areas_types_type_code",
        schema="ref_geo",
        table_name="bib_area_types",
        columns=["type_code"],
        unique=True,
    )
