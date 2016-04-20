"""Added index for itemrevision created_date

Revision ID: 6b9d673d8e30
Revises: 1727fb4309d8
Create Date: 2016-04-01 09:39:35.148502

"""

# revision identifiers, used by Alembic.
revision = '6b9d673d8e30'
down_revision = '1727fb4309d8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ix_itemrevision_date_created', 'itemrevision', ['date_created'], unique=False)


def downgrade():
    op.drop_index('ix_itemrevision_date_created', table_name='itemrevision')