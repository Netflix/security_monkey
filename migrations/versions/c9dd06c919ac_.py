"""Add fields to ItemAudit table to support a future revamp of the issue system.

Mostly not using these new fields yet.

Action Instructions will hold information for how the user can fix the issue.
Background Information will hold information on why something is a problem, likely with links to AWS documentation for the user to read more.
Origin will hold the statement causing the issue.  Hopefully the UI can use this to highlight the offending part of an item policy.
Origin Summary will hold a summary of the Origin.  A JSON Policy statement may be summarized as something like "S3 READ FROM * TO s3:mybucket".
Class UUID will be used so that the text (itemaudit.issue, itemaudit.notes) can be changed in the future without losing justifications.

Revision ID: c9dd06c919ac
Revises: b8ccf5b8089b
Create Date: 2017-09-05 17:21:08.162000

"""

# revision identifiers, used by Alembic.
revision = 'c9dd06c919ac'
down_revision = 'b8ccf5b8089b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('itemaudit', sa.Column('action_instructions', sa.Text(), nullable=True))
    op.add_column('itemaudit', sa.Column('background_info', sa.Text(), nullable=True))
    op.add_column('itemaudit', sa.Column('origin', sa.Text(), nullable=True))
    op.add_column('itemaudit', sa.Column('origin_summary', sa.Text(), nullable=True))
    op.add_column('itemaudit', sa.Column('class_uuid', sa.VARCHAR(length=32), nullable=True))


def downgrade():
    op.drop_column('itemaudit', 'action_instructions')
    op.drop_column('itemaudit', 'background_info')
    op.drop_column('itemaudit', 'class_uuid')
    op.drop_column('itemaudit', 'origin')
    op.drop_column('itemaudit', 'origin_summary')