"""Renaming rds to rdssecuritygroup

Revision ID: 1a863bd1acb1
Revises: 0ae4ef82b244
Create Date: 2016-09-20 20:22:19.687138

"""

# revision identifiers, used by Alembic.
revision = '1a863bd1acb1'
down_revision = '0ae4ef82b244'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Session = sessionmaker()
Base = declarative_base()


class Technology(Base):
    __tablename__ = 'technology'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(32))


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    rds_tech = session.query(Technology).filter(Technology.name == 'rds').first()
    if rds_tech:
        rds_tech.name = 'rdssecuritygroup'
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    rds_tech = session.query(Technology).filter(Technology.name == 'rdssecuritygroup').first()
    if rds_tech:
        rds_tech.name = 'rds'
    session.commit()
