"""Added index for itemrevision created_date

Revision ID: 6b9d673d8e30
Revises: 2ea41f4610fd
Create Date: 2016-04-01 09:39:35.148502

"""

# revision identifiers, used by Alembic.
revision = '6b9d673d8e30'
down_revision = '2ea41f4610fd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ix_itemrevision_date_created', 'itemrevision', ['date_created'], unique=False)


def downgrade():
    op.drop_index('ix_itemrevision_date_created', table_name='itemrevision')
