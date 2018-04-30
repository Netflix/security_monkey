"""lengthen Account.name

Revision ID: 00c1dabdbe85
Revises: ea2739ecd874
Create Date: 2018-03-09 14:29:17.620533

"""

# revision identifiers, used by Alembic.
revision = '00c1dabdbe85'
down_revision = 'ea2739ecd874'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('account', 'name',
        existing_type=sa.VARCHAR(length=32),
        type_=sa.String(length=50),
        existing_nullable=True)


def downgrade():
    op.alter_column('account', 'name',
        existing_type=sa.VARCHAR(length=50),
        type_=sa.String(length=32),
        existing_nullable=True)
