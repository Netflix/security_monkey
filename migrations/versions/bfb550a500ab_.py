"""Adding ARN column and latest_revision_complete_hash and latest_revision_durable_hash to item table

Revision ID: bfb550a500ab
Revises: ae5c0a6aebb3
Create Date: 2016-06-23 21:16:35.951815

"""

# revision identifiers, used by Alembic.
revision = 'bfb550a500ab'
down_revision = 'ae5c0a6aebb3'

from alembic import op
import sqlalchemy as sa
import datetime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as BaseSession, relationship, deferred
import hashlib
import json
from copy import deepcopy
import dpath.util
from dpath.exceptions import PathNotFound
from six import text_type


Session = sessionmaker()
Base = declarative_base()


class Technology(Base):
    __tablename__ = 'technology'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(32))
    items = relationship("Item", backref="technology")


class Item(Base):
    __tablename__ = 'item'
    id = sa.Column(sa.Integer, primary_key=True)
    arn = sa.Column(sa.Text(), nullable=True, index=True, unique=True)
    latest_revision_id = sa.Column(sa.Integer, nullable=True)
    latest_revision_complete_hash = sa.Column(sa.String(32), index=True)
    latest_revision_durable_hash = sa.Column(sa.String(32), index=True)
    tech_id = sa.Column(sa.Integer, sa.ForeignKey("technology.id"), nullable=False)
    revisions = relationship("ItemRevision", backref="item", cascade="all, delete, delete-orphan", order_by="desc(ItemRevision.date_created)", lazy="dynamic")


class ItemRevision(Base):
    """
    Every new configuration for an item is saved in a new ItemRevision.
    """
    __tablename__ = "itemrevision"
    id = sa.Column(sa.Integer, primary_key=True)
    active = sa.Column(sa.Boolean())
    config = deferred(sa.Column(JSON))
    item_id = sa.Column(sa.Integer, sa.ForeignKey("item.id"), nullable=False)
    date_created = sa.Column(sa.DateTime(), default=datetime.datetime.utcnow, nullable=False, index=True)


prims = [int, str, text_type, bool, float, type(None)]


def sub_list(l):
    """
    Recursively walk a datastructrue sorting any lists along the way.

    :param l: list
    :return: sorted list, where any child lists are also sorted.
    """
    r = []

    for i in l:
        if type(i) in prims:
            r.append(i)
        elif type(i) is list:
            r.append(sub_list(i))
        elif type(i) is dict:
            r.append(sub_dict(i))
        else:
            print("Unknown Type: {}".format(type(i)))
    r = sorted(r)
    return r


def sub_dict(d):
    """
    Recursively walk a datastructure sorting any lists along the way.

    :param d: dict
    :return: dict where any lists, even those buried deep in the structure, have been sorted.
    """
    r = {}
    for k in d:
        if type(d[k]) in prims:
            r[k] = d[k]
        elif type(d[k]) is list:
            r[k] = sub_list(d[k])
        elif type(d[k]) is dict:
            r[k] = sub_dict(d[k])
        else:
            print("Unknown Type: {}".format(type(d[k])))
    return r


def retrieve_arn(config):
    """
    See issue #374. SM does not currently store ARNs in a consistent place.

    :param config: itemrevision config dict
    :return: ARN, if we can find it
    """
    if config.get('arn'):
        return config.get('arn')

    if config.get('Arn'):
        return config.get('Arn')

    if config.get('CertificateArn'):
        return config.get('CertificateArn')

    if config.get('group', {}).get('arn'):
        return config.get('group', {}).get('arn')

    if config.get('role', {}).get('arn'):
        return config.get('role', {}).get('arn')

    if config.get('user', {}).get('arn'):
        return config.get('user', {}).get('arn')

    return None


def hash_item(item, ephemeral_paths):
    """
    Finds the hash of a dict.

    :param item: dictionary, representing an item tracked in security_monkey
    :return: hash of the json dump of the item
    """
    complete = hash_config(item)
    durable = durable_hash(item, ephemeral_paths)
    return complete, durable


def durable_hash(item, ephemeral_paths):
    """
    Remove all ephemeral paths from the item and return the hash of the new structure.

    :param item: dictionary, representing an item tracked in security_monkey
    :return: hash of the sorted json dump of the item with all ephemeral paths removed.
    """
    durable_item = deepcopy(item)
    for path in ephemeral_paths:
        try:
            dpath.util.delete(durable_item, path, separator='$')
        except PathNotFound:
            pass
    return hash_config(durable_item)


def hash_config(config):
    item = sub_dict(config)
    item_str = json.dumps(item, sort_keys=True)
    item_hash = hashlib.md5(item_str) # nosec: not used for security
    return item_hash.hexdigest()


def ephemeral_paths_for_item(item):
    technology = item.technology.name

    paths = {
        'redshift': [
            "RestoreStatus",
            "ClusterStatus",
            "ClusterParameterGroups$ParameterApplyStatus",
            "ClusterParameterGroups$ClusterParameterStatusList$ParameterApplyErrorDescription",
            "ClusterParameterGroups$ClusterParameterStatusList$ParameterApplyStatus",
            "ClusterRevisionNumber"
        ],
        'securitygroup': ["assigned_to"],
        'iamuser': [
            "user$password_last_used",
            "accesskeys$*$LastUsedDate",
            "accesskeys$*$Region",
            "accesskeys$*$ServiceName"
        ]
    }

    return paths.get(technology, [])


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('arn', sa.Text(), nullable=True))
    op.add_column('item', sa.Column('latest_revision_complete_hash', sa.String(32), nullable=True))
    op.add_column('item', sa.Column('latest_revision_durable_hash', sa.String(32), nullable=True))
    op.create_index('ix_item_arn', 'item', ['arn'], unique=True)
    op.create_index('ix_item_name', 'item', ['name'], unique=False)
    op.create_index('ix_item_latest_revision_complete_hash', 'item', ['latest_revision_complete_hash'], unique=False)
    op.create_index('ix_item_latest_revision_durable_hash', 'item', ['latest_revision_durable_hash'], unique=False)
    ### end Alembic commands ###

    query = session.query(Item) \
        .join((ItemRevision, Item.latest_revision_id == ItemRevision.id)) \
        .filter(ItemRevision.active == True)

    for item in query.all():
        revision = item.revisions.first()
        arn = retrieve_arn(revision.config)
        if arn and u'arn:aws:iam::aws:policy' not in arn:
            item.arn = arn

        ephemeral_paths = ephemeral_paths_for_item(item)
        complete_hash, durable_hash = hash_item(revision.config, ephemeral_paths)
        item.latest_revision_complete_hash = complete_hash
        item.latest_revision_durable_hash = durable_hash

    session.commit()


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_item_name', table_name='item')
    op.drop_index('ix_item_arn', table_name='item')
    op.drop_index('ix_item_latest_revision_durable_hash', table_name='item')
    op.drop_index('ix_item_latest_revision_complete_hash', table_name='item')
    op.drop_column('item', 'arn')
    op.drop_column('item', 'latest_revision_complete_hash')
    op.drop_column('item', 'latest_revision_durable_hash')
    ### end Alembic commands ###
