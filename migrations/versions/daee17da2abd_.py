"""Rename the new Glacier watcher from 'vault' to 'glacier'.

Revision ID: daee17da2abd
Revises: c9dd06c919ac
Create Date: 2017-09-06 17:21:08.162000

"""

# revision identifiers, used by Alembic.
revision = 'daee17da2abd'
down_revision = 'c9dd06c919ac'

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
    # Rename vault to glacier
    bind = op.get_bind()
    session = Session(bind=bind)
    glacier_tech = session.query(Technology).filter(Technology.name == 'vault').first()
    if glacier_tech:
        glacier_tech.name = 'glacier'
    session.commit()

def downgrade():
    # Rename glacier to vault
    bind = op.get_bind()
    session = Session(bind=bind)
    glacier_tech = session.query(Technology).filter(Technology.name == 'glacier').first()
    if glacier_tech:
        glacier_tech.name = 'vault'
    session.commit()
