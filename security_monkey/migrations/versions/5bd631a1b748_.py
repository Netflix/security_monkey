"""Updating fixed flag in the issue table to be not nullable.

Revision ID: 5bd631a1b748
Revises: 4ac52090a637
Create Date: 2017-09-26 11:05:23.060909

"""

# revision identifiers, used by Alembic.
revision = '5bd631a1b748'
down_revision = '4ac52090a637'

from alembic import op
import sqlalchemy as sa

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Session = sessionmaker()
Base = declarative_base()


class ItemAudit(Base):
    __tablename__ = 'itemaudit'
    id = sa.Column(sa.Integer, primary_key=True)
    fixed = sa.Column(sa.Boolean)


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # update itemaudit set fixed = False where fixed is NULL
    session.query(ItemAudit).filter(ItemAudit.fixed==None).update(dict(fixed=False))
    session.commit()

    # Make column not nullable:
    op.alter_column('itemaudit', 'fixed', nullable=False)


def downgrade():
    # Make column nullable:
    op.alter_column('itemaudit', 'fixed', nullable=True)