"""Updating max length of Item name from 128 characters to 285.  AWS Max size is 255.  Add 30 chars for Security_monkey specific metadata.

Revision ID: 331ca47ce8ad
Revises: c01df2202a9
Create Date: 2014-08-26 12:40:02.577519

"""

# revision identifiers, used by Alembic.
revision = '331ca47ce8ad'
down_revision = 'c01df2202a9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('item', 'name', type_=sa.String(285), existing_type=sa.String(length=128), nullable=True)


def downgrade():
    op.alter_column('item', 'name', type_=sa.String(128), existing_type=sa.String(length=285), nullable=True)

