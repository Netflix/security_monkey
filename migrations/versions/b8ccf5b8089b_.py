"""Fetch the S3 Canonical IDs for all active AWS accounts.

Revision ID: b8ccf5b8089b
Revises: 908b0085d28d
Create Date: 2017-03-23 11:00:43.792538
Author: Mike Grima <mgrima@netflix.com>

"""

# revision identifiers, used by Alembic.
import sqlalchemy as sa

from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from security_monkey.manage import fetch_aws_canonical_ids

Session = sessionmaker()
Base = declarative_base()

revision = 'b8ccf5b8089b'
down_revision = '908b0085d28d'

class Account(Base):
    """
    Meant to model AWS accounts.
    """
    __tablename__ = "account"
    id = sa.Column(sa.Integer, primary_key=True)
    active = sa.Column(sa.Boolean())
    third_party = sa.Column(sa.Boolean())
    name = sa.Column(sa.String(32), index=True, unique=True)
    notes = sa.Column(sa.String(256))
    identifier = sa.Column(sa.String(256))  # Unique id of the account, the number for AWS.
    account_type_id = sa.Column(sa.Integer, sa.ForeignKey("account_type.id"), nullable=False)
    unique_const = sa.UniqueConstraint('account_type_id', 'identifier')


def upgrade():
    print("[-->] Adding canonical IDs to all AWS accounts that are active...")
    bind = op.get_bind()
    session = Session(bind=bind)

    # If there are currently no accounts, then skip... (avoids alembic issues...)
    accounts = session.query(Account).all()
    if len(accounts) > 0:
        fetch_aws_canonical_ids(True)

    print("[@] Completed adding canonical IDs to all active AWS accounts...")


def downgrade():
    # No need to go back...
    pass
