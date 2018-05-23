"""Detect and remove duplicate items in the database.

Revision ID: 7c54b06e227b
Revises: 11f081cf54e2
Create Date: 2018-04-30 12:31:47.748649

"""

# revision identifiers, used by Alembic.
import datetime

revision = '7c54b06e227b'
down_revision = '11f081cf54e2'

from alembic import op
from sqlalchemy import Column, Boolean, Integer, String, JSON, ForeignKey, Text, BigInteger, DateTime, Unicode, text, \
    Table

from sqlalchemy.orm import sessionmaker, relationship, deferred

from sqlalchemy.ext.declarative import declarative_base

Session = sessionmaker()
Base = declarative_base()


class AccountType(Base):
    """
    Defines the type of account based on where the data lives, e.g. AWS.
    """
    __tablename__ = "account_type"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)


class Account(Base):
    """
    Meant to model AWS accounts.
    """
    __tablename__ = "account"
    id = Column(Integer, primary_key=True)
    active = Column(Boolean())
    third_party = Column(Boolean())
    name = Column(String(50), index=True, unique=True)
    notes = Column(String(256))
    identifier = Column(String(256), unique=True)  # Unique id of the account, the number for AWS.
    account_type_id = Column(Integer, ForeignKey("account_type.id"), nullable=False)


class AccountTypeCustomValues(Base):
    """
    Defines the values for custom fields defined in AccountTypeCustomFields.
    """
    __tablename__ = "account_type_values"
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    value = Column(String(256))
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)


class ExceptionLogs(Base):
    """
    This table stores all exceptions that are encountered, and provides metadata and context
    around the exceptions.
    """
    __tablename__ = "exceptions"
    id = Column(BigInteger, primary_key=True)
    source = Column(String(256), nullable=False, index=True)
    occurred = Column(DateTime, default=datetime.datetime.utcnow(), nullable=False)
    ttl = Column(DateTime, default=(datetime.datetime.utcnow() + datetime.timedelta(days=10)), nullable=False)
    type = Column(String(256), nullable=False, index=True)
    message = Column(String(512))
    stacktrace = Column(Text)
    region = Column(String(32), nullable=True, index=True)

    tech_id = Column(Integer, ForeignKey("technology.id", ondelete="CASCADE"), index=True)
    item_id = Column(Integer, ForeignKey("item.id", ondelete="CASCADE"), index=True)
    account_id = Column(Integer, ForeignKey("account.id", ondelete="CASCADE"), index=True)


issue_item_association = Table(
    'issue_item_association',
    Base.metadata,
    Column('super_issue_id', Integer, ForeignKey('itemaudit.id'), primary_key=True),
    Column('sub_item_id', Integer, ForeignKey('item.id'), primary_key=True)
)


class ItemAudit(Base):
    """
    Meant to model an issue attached to a single item.
    """
    __tablename__ = "itemaudit"
    id = Column(Integer, primary_key=True)
    score = Column(Integer)
    issue = Column(String(512))
    notes = Column(String(1024))
    action_instructions = Column(Text(), nullable=True)
    background_info = Column(Text(), nullable=True)
    origin = Column(Text(), nullable=True)
    origin_summary = Column(Text(), nullable=True)
    class_uuid = Column(String(32), nullable=True)
    fixed = Column(Boolean, default=False, nullable=False)
    justified = Column(Boolean)
    justified_user_id = Column(Integer, ForeignKey("user.id"), nullable=True, index=True)
    justification = Column(String(512))
    justified_date = Column(DateTime(), default=datetime.datetime.utcnow, nullable=True)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False, index=True)
    auditor_setting_id = Column(Integer, ForeignKey("auditorsettings.id"), nullable=True, index=True)
    sub_items = relationship("Item", secondary=issue_item_association, backref="super_issues")


class Item(Base):
    """
    Meant to model a specific item, like an instance of a security group.
    """
    __tablename__ = "item"
    id = Column(Integer, primary_key=True)
    region = Column(String(32), index=True)
    name = Column(String(303), index=True)
    arn = Column(Text(), nullable=True, index=True, unique=True)
    latest_revision_complete_hash = Column(String(32), index=True)
    latest_revision_durable_hash = Column(String(32), index=True)
    tech_id = Column(Integer, ForeignKey("technology.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False, index=True)
    latest_revision_id = Column(Integer, nullable=True)
    comments = relationship("ItemComment", backref="revision", cascade="all, delete, delete-orphan")
    revisions = relationship("ItemRevision", backref="item", cascade="all, delete, delete-orphan")
    issues = relationship("ItemAudit", backref="item", cascade="all, delete, delete-orphan")
    cloudtrail_entries = relationship("CloudTrailEntry", backref="item", cascade="all, delete, delete-orphan")
    issues = relationship("ItemAudit", backref="item", cascade="all, delete, delete-orphan",
                          foreign_keys="ItemAudit.item_id")
    exceptions = relationship("ExceptionLogs", backref="item", cascade="all, delete, delete-orphan")


class ItemComment(Base):
    """
    The Web UI allows users to add comments to items.
    """
    __tablename__ = "itemcomment"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('item.id'), nullable=False, index=True)
    date_created = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False)
    text = Column(Unicode(1024))


class ItemRevisionComment(Base):
    """
    The Web UI allows users to add comments to revisions.
    """
    __tablename__ = "itemrevisioncomment"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    revision_id = Column(Integer, ForeignKey('itemrevision.id'), nullable=False, index=True)
    date_created = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False)
    text = Column(Unicode(1024))


class ItemRevision(Base):
    """
    Every new configuration for an item is saved in a new ItemRevision.
    """
    __tablename__ = "itemrevision"
    id = Column(Integer, primary_key=True)
    active = Column(Boolean())
    config = deferred(Column(JSON))
    date_created = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False, index=True)
    date_last_ephemeral_change = Column(DateTime(), nullable=True, index=True)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False, index=True)
    comments = relationship("ItemRevisionComment", backref="revision", cascade="all, delete, delete-orphan")
    cloudtrail_entries = relationship("CloudTrailEntry", backref="revision", cascade="all, delete, delete-orphan")


class CloudTrailEntry(Base):
    """
    Bananapeel (the security_monkey rearchitecture) will use this table to
    correlate CloudTrail entries to item revisions.
    """
    __tablename__ = 'cloudtrail'
    id = Column(Integer, primary_key=True)
    event_id = Column(String(36), index=True, unique=True)
    request_id = Column(String(36), index=True)
    event_source = Column(String(64), nullable=False)
    event_name = Column(String(64), nullable=False)
    event_time = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False, index=True)
    request_parameters = deferred(Column(JSON))
    responseElements = deferred(Column(JSON))
    source_ip = Column(String(45))
    user_agent = Column(String(300))
    full_entry = deferred(Column(JSON))
    user_identity = deferred(Column(JSON))
    user_identity_arn = Column(String(300), index=True)
    revision_id = Column(Integer, ForeignKey('itemrevision.id'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('item.id'), nullable=False, index=True)


class Technology(Base):
    """
    meant to model AWS primitives (elb, s3, iamuser, iamgroup, etc.)
    """
    __tablename__ = 'technology'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), index=True, unique=True)  # elb, s3, iamuser, iamgroup, etc.


def upgrade():
    """
    Need to detect duplicate items.
    This needs to be done by looking for all items with the same: region, name, tech_id, account_id.
    With these items, pick the one that has the bigger latest_revision_id and delete the others.
    :return:
    """
    bind = op.get_bind()
    session = Session(bind=bind)

    items_reference = {}
    items_to_delete = []

    print("[-->] Looking for duplicate items in the Item table... This may take a while...")

    # I've waisted way too much time looking for the proper SQLAlchemy way of doing this...
    result = session.execute(text("""(SELECT o.id, o.region, o.name, o.tech_id, o.account_id, o.latest_revision_id
      FROM item o WHERE (
        SELECT count(*) FROM item i
            WHERE
                o.region = i.region AND
                o.name = i.name AND
                o.account_id = i.account_id AND
                o.tech_id = i.tech_id) > 1);"""))

    for r in result:
        index = "{region}-{name}-{tech_id}-{account_id}".format(region=r[1], name=r[2], tech_id=r[3], account_id=r[4])
        if not items_reference.get(index):
            items_reference[index] = r
        else:
            # Compare the latest revision id -- we only want to keep the larger (newest) one.
            if items_reference[index][5] > r[5]:
                items_to_delete.append(r)
            else:
                items_to_delete.append(items_reference[index])
                items_reference[index] = r

    if not items_to_delete:
        print("[@] No duplicate items found!")
    else:
        print("[!] Duplicate items found... Deleting them...")
        for duplicate in items_to_delete:
            # Get the SQLAlchemy Item to delete (simplifies cascades and things):
            db_item = session.query(Item).filter(Item.id == duplicate[0]).scalar()
            session.delete(db_item)
            # session.execute(delete(Item, Item.id == duplicate[0]))
            print("[-] Marked duplicate item for deletion: {}".format(duplicate[2]))

        print("[-->] Deleting...")
        session.commit()
        print("[@] Completed deleting duplicate items!")


def downgrade():
    """No downgrade necessary."""
    pass
