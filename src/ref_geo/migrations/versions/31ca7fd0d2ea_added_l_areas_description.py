"""Added l_areas description

Revision ID: 31ca7fd0d2ea
Revises: 1fdac7036dd9
Create Date: 2025-01-16 12:29:32.550025

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1ca7fd0d2ea"
down_revision = "1fdac7036dd9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name="l_areas",
        schema="ref_geo",
        column=sa.Column("description", sa.UnicodeText(), server_default=None),
    )


def downgrade():
    op.drop_column(table_name="l_areas", column_name="description", schema="ref_geo")
