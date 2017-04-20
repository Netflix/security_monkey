"""Please run "monkey fetch_aws_canonical_ids"

Revision ID: b8ccf5b8089b
Revises: 908b0085d28d
Create Date: 2017-03-23 11:00:43.792538
Author: Mike Grima <mgrima@netflix.com>, No-op'ed by Patrick

"""

# revision identifiers, used by Alembic.
import sqlalchemy as sa

from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

revision = 'b8ccf5b8089b'
down_revision = '908b0085d28d'


def upgrade():
    # This revision has been replaced with a no-op after numerous reports of db upgrade problems.
    # We recommend you run:
    #   monkey fetch_aws_canonical_ids
    pass


def downgrade():
    # No need to go back...
    pass
