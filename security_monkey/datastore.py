#     Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
.. module: security_monkey.datastore
    :platform: Unix
    :synopsis: Contains the SQLAlchemy models and a few helper methods.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from deepdiff import DeepHash
from flask_security.core import UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, desc

from .auth.models import RBACUserMixin

from security_monkey import db, app

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Unicode, Text
from sqlalchemy.dialects.postgresql import CIDR
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, column_property, load_only
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, func

from sqlalchemy.orm import deferred

import datetime
import traceback

import dpath.util
from deepdiff import DeepHash
from dpath.exceptions import PathNotFound
from copy import deepcopy


def durable_hash(config, ephemeral_paths):
    durable_item = deepcopy(config)
    for path in ephemeral_paths:
        try:
            dpath.util.delete(durable_item, path, separator='$')
        except PathNotFound:
            pass
    return DeepHash(durable_item)[durable_item]


def hash_item(config, ephemeral_paths):
    """
    Finds the hash of a dict.

    :param ephemeral_paths:
    :param config:
    :param item: dictionary, typically representing an item tracked in SM
                 such as an IAM role
    :return: hash of the json dump of the item
    """
    complete = DeepHash(config)[config]
    durable = durable_hash(config, ephemeral_paths)
    return complete, durable


association_table = db.Table(
    'association',
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('account_id', Integer, ForeignKey('account.id'), primary_key=True)
)


class AccountType(db.Model):
    """
    Defines the type of account based on where the data lives, e.g. AWS.
    """
    __tablename__ = "account_type"
    id = Column(Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    accounts = relationship("Account", backref="account_type")


class Account(db.Model):
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
    items = relationship("Item", backref="account", cascade="all, delete, delete-orphan")
    issue_categories = relationship("AuditorSettings", backref="account")
    account_type_id = Column(Integer, ForeignKey("account_type.id"), nullable=False)
    custom_fields = relationship("AccountTypeCustomValues", lazy="immediate", cascade="all, delete, delete-orphan")
    unique_const = UniqueConstraint('account_type_id', 'identifier')

    # 'lazy' is required for the Celery scheduler to reference the type:
    type = relationship("AccountType", backref="account_type", lazy="immediate")
    exceptions = relationship("ExceptionLogs", backref="account", cascade="all, delete, delete-orphan")

    def getCustom(self, name):
        for field in self.custom_fields:
            if field.name == name:
                return field.value
        return None


class AccountTypeCustomValues(db.Model):
    """
    Defines the values for custom fields defined in AccountTypeCustomFields.
    """
    __tablename__ = "account_type_values"
    id = Column(Integer, primary_key=True)
    name = Column(db.String(64))
    value = db.Column(db.String(256))
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    unique_const = UniqueConstraint('account_id', 'name')


class Technology(db.Model):
    """
    meant to model AWS primitives (elb, s3, iamuser, iamgroup, etc.)
    """
    __tablename__ = 'technology'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), index=True, unique=True)  # elb, s3, iamuser, iamgroup, etc.
    items = relationship("Item", backref="technology")
    issue_categories = relationship("AuditorSettings", backref="technology")
    ignore_items = relationship("IgnoreListEntry", backref="technology")

    exceptions = relationship("ExceptionLogs", backref="technology", cascade="all, delete, delete-orphan")


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'), primary_key=True)
)


class Role(db.Model, RoleMixin):
    """
    Used by Flask-Login / the auth system to check user permissions.
    """
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(UserMixin, db.Model, RBACUserMixin):
    """
    Used by Flask-Security and Flask-Login.
    Represents a user of Security Monkey.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    daily_audit_email = Column(Boolean())
    change_reports = Column(String(32))  # All, OnlyWithIssues, None

    # Flask-Security SECURITY_TRACKABLE
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    login_count = Column(Integer)
    # Why 45 characters for IP Address ?
    # See http://stackoverflow.com/questions/166132/maximum-length-of-the-textual-representation-of-an-ipv6-address/166157#166157
    last_login_ip = Column(db.String(45))
    current_login_ip = Column(db.String(45))

    accounts = relationship("Account", secondary=association_table)
    item_audits = relationship("ItemAudit", uselist=False, backref="user")
    revision_comments = relationship("ItemRevisionComment", backref="user")
    item_comments = relationship("ItemComment", backref="user")
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    role = db.Column(db.String(30), default="View")

    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)


issue_item_association = db.Table('issue_item_association',
    Column('super_issue_id', Integer, ForeignKey('itemaudit.id'), primary_key=True),
    Column('sub_item_id', Integer, ForeignKey('item.id'), primary_key=True)
)


class ItemAudit(db.Model):
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
    sub_items = relationship("Item", secondary=issue_item_association, back_populates="issues")
    item = relationship("Item")  # TODO: Remove this when the issue system is refactored.

    def __str__(self):
        return "Issue: [{issue}] Score: {score} Fixed: {fixed} Justified: {justified}\nNotes: {notes}\n".format(
            issue=self.issue,
            score=self.score,
            fixed=self.fixed,
            justified=self.justified,
            notes=self.notes)

    def __repr__(self):
        return self.__str__()

    def sub_ids(self):
        item_ids = []
        for sub_item in self.sub_items:
            item_ids.append(sub_item.id)
        return str(item_ids.sort())

    def key(self):
        return '{issue} -- {notes} -- {score} -- {subids}'.format(
            issue=self.issue,
            notes=self.notes,
            score=self.score,
            subids=self.sub_ids())

    def copy_unlinked(self):
        """
        Used to address SQLAlchemy annoyances when the auditor saves issues. For some reason... if we don't
        make a copy of this object, SQLAlchemy complains that it's already attached to item...
        """
        return ItemAudit(score=self.score, issue=self.issue, notes=self.notes,
                         action_instructions=self.action_instructions,
                         background_info=self.background_info, origin=self.origin,
                         origin_summary=self.origin_summary, class_uuid=self.class_uuid,
                         fixed=self.fixed, justified=self.justified, justified_user_id=self.justified_user_id,
                         justification=self.justification, justified_date=self.justified_date,
                         auditor_setting_id=self.auditor_setting_id)


class AuditorSettings(db.Model):
    """
    This table contains auditor disable settings.
    """
    __tablename__ = "auditorsettings"
    id = Column(Integer, primary_key=True)
    disabled = Column(Boolean(), nullable=False)
    issue_text = Column(String(512), nullable=True)
    auditor_class = Column(String(128))
    issues = relationship("ItemAudit", backref="auditor_setting", cascade="all, delete, delete-orphan")
    tech_id = Column(Integer, ForeignKey("technology.id"), index=True)
    account_id = Column(Integer, ForeignKey("account.id"), index=True)
    unique_const = UniqueConstraint('account_id', 'issue_text', 'tech_id')


class Item(db.Model):
    """
    Meant to model a specific item, like an instance of a security group.
    """
    __tablename__ = "item"
    id = Column(Integer, primary_key=True)
    region = Column(String(32), index=True)
    # Max AWS name = 255 chars.  Add 48 chars for ' (sg-12345678901234567 in vpc-12345678901234567)'
    name = Column(String(303), index=True)
    arn = Column(Text(), nullable=True, index=True, unique=True)
    latest_revision_complete_hash = Column(String(64), index=True)
    latest_revision_durable_hash = Column(String(64), index=True)
    tech_id = Column(Integer, ForeignKey("technology.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False, index=True)
    latest_revision_id = Column(Integer, nullable=True)
    comments = relationship("ItemComment", backref="revision", cascade="all, delete, delete-orphan",
                            order_by="ItemComment.date_created")
    revisions = relationship("ItemRevision", backref="item", cascade="all, delete, delete-orphan",
                             order_by="desc(ItemRevision.date_created)", lazy="dynamic")
    cloudtrail_entries = relationship("CloudTrailEntry", backref="item", cascade="all, delete, delete-orphan",
                                      order_by="CloudTrailEntry.event_time")
    issues = relationship("ItemAudit", secondary=issue_item_association, back_populates="sub_items",
                          single_parent=True, cascade="all, delete, delete-orphan")
    exceptions = relationship("ExceptionLogs", backref="item", cascade="all, delete, delete-orphan")

    @hybrid_property
    def score(self):
        return db.session.query(
            func.cast(
                func.sum(ItemAudit.score),
                Integer)
        ).filter(
            ItemAudit.item_id == self.id,
            ItemAudit.auditor_setting_id == AuditorSettings.id,
            ItemAudit.fixed == False,
            AuditorSettings.disabled == False).one()[0] or 0

    @score.expression
    def score(cls):
        return select([func.sum(ItemAudit.score)]). \
            where(ItemAudit.item_id == cls.id). \
            where(ItemAudit.auditor_setting_id == AuditorSettings.id). \
            where(ItemAudit.fixed == False). \
            where(AuditorSettings.disabled == False). \
            label('item_score')

    @hybrid_property
    def unjustified_score(self):
        return db.session.query(
            func.cast(
                func.sum(ItemAudit.score),
                Integer)
        ).filter(
            ItemAudit.item_id == self.id,
            ItemAudit.justified == False,
            ItemAudit.fixed == False,
            ItemAudit.auditor_setting_id == AuditorSettings.id,
            AuditorSettings.disabled == False).one()[0] or 0

    @unjustified_score.expression
    def unjustified_score(cls):
        return select([func.sum(ItemAudit.score)]). \
            where(ItemAudit.item_id == cls.id). \
            where(ItemAudit.justified == False). \
            where(ItemAudit.fixed == False). \
            where(ItemAudit.auditor_setting_id == AuditorSettings.id). \
            where(AuditorSettings.disabled == False). \
            label('item_unjustified_score')

    issue_count = column_property(
        select([func.count(ItemAudit.id)])
        .where(ItemAudit.item_id == id)
        .where(ItemAudit.fixed == False)
        .where(ItemAudit.auditor_setting_id == AuditorSettings.id)
        .where(AuditorSettings.disabled == False),
        deferred=True
    )

    @hybrid_property
    def latest_config(self):
        """Returns the config from the latest item revision."""
        return db.session.query(ItemRevision).filter(ItemRevision.id == self.latest_revision_id).one().config


class ItemComment(db.Model):
    """
    The Web UI allows users to add comments to items.
    """
    __tablename__ = "itemcomment"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey('item.id'), nullable=False, index=True)
    date_created = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False)
    text = Column(Unicode(1024))

    def __str__(self):
        return "User [{user}]({date}): {text}".format(
            user=self.user.email,
            date=str(self.date_created),
            text=self.text
        )

    def __repr__(self):
        return self.__str__()


class ItemRevision(db.Model):
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
    comments = relationship("ItemRevisionComment", backref="revision", cascade="all, delete, delete-orphan",
                            order_by="ItemRevisionComment.date_created")
    cloudtrail_entries = relationship("CloudTrailEntry", backref="revision", cascade="all, delete, delete-orphan",
                                      order_by="CloudTrailEntry.event_time")


class CloudTrailEntry(db.Model):
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


class ItemRevisionComment(db.Model):
    """
    The Web UI allows users to add comments to revisions.
    """
    __tablename__ = "itemrevisioncomment"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    revision_id = Column(Integer, ForeignKey('itemrevision.id'), nullable=False, index=True)
    date_created = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False)
    text = Column(Unicode(1024))


class NetworkWhitelistEntry(db.Model):
    """
    This table contains user-entered CIDR's that security_monkey
    will not alert on.
    """
    __tablename__ = "networkwhitelist"
    id = Column(Integer, primary_key=True)
    name = Column(String(512))
    notes = Column(String(512))
    cidr = Column(CIDR)


class IgnoreListEntry(db.Model):
    """
    This table contains user-entered prefixes that security_monkey
    will ignore when slurping the AWS config.
    """
    __tablename__ = "ignorelist"
    id = Column(Integer, primary_key=True)
    prefix = Column(String(512))
    notes = Column(String(512))
    tech_id = Column(Integer, ForeignKey("technology.id"), nullable=False, index=True)


class ExceptionLogs(db.Model):
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


class ItemAuditScore(db.Model):
    """
    This table maps scores to audit methods, allowing for configurable scores.
    """
    __tablename__ = "itemauditscores"
    id = Column(Integer, primary_key=True)
    technology = Column(String(128), nullable=False)
    method = Column(String(256), nullable=False)
    score = Column(Integer, nullable=False)
    disabled = Column(Boolean, default=False)
    account_pattern_scores = relationship("AccountPatternAuditScore", backref="itemauditscores",
                                          cascade="all, delete, delete-orphan")
    __table_args__ = (UniqueConstraint('technology', 'method'), )


    def add_or_update_pattern_score(self, account_type, field, pattern, score):
        db_pattern_score = self.get_account_pattern_audit_score(account_type, field, pattern)
        if db_pattern_score is not None:
            db_pattern_score.score = score
        else:
            db_pattern_score = AccountPatternAuditScore(account_type=account_type,
                                                        account_field=field,
                                                        account_pattern=pattern,
                                                        score=score)

            self.account_pattern_scores.append(db_pattern_score)

    def get_account_pattern_audit_score(self, account_type, field, pattern):
        for db_pattern_score in self.account_pattern_scores:
            if db_pattern_score.account_field == field and \
                    db_pattern_score.account_pattern == pattern and db_pattern_score.account_type == account_type:
                return db_pattern_score


class AccountPatternAuditScore(db.Model):
    """
    This table allows the value(s) of an account field to be mapped to scores, allowing for
    configurable scores by account.
    """
    __tablename__ = "accountpatternauditscore"
    id = Column(Integer, primary_key=True)
    account_type = Column(String(80), nullable=False)
    account_field = Column(String(128), nullable=False)
    account_pattern = Column(String(128), nullable=False)
    score = Column(Integer, nullable=False)
    itemauditscores_id = Column(Integer, ForeignKey("itemauditscores.id"), nullable=False)


class WatcherConfig(db.Model):
    """
    Defines watcher configurations for interval and active
    """
    __tablename__ = "watcher_config"
    id = Column(Integer, primary_key=True)
    index = Column(db.String(80), unique=True)
    interval = Column(Integer, nullable=False)
    active = Column(Boolean(), nullable=False)


class Datastore(object):
    def __init__(self, debug=False):
        pass

    def get_all_ctype_filtered(self, tech=None, account=None, region=None, name=None, include_inactive=False):
        """
        Returns a list of Items joined with their most recent ItemRevision,
        potentially filtered by the criteria above.
        """
        item_map = {}
        query = Item.query
        if tech:
            query = query.join((Technology, Item.tech_id == Technology.id)).filter(Technology.name == tech)
        if account:
            query = query.join((Account, Item.account_id == Account.id)).filter(Account.name == account)

        filter_by = {'region': region, 'name': name}
        for k, v in list(filter_by.items()):
            if not v:
                del filter_by[k]

        query = query.filter_by(**filter_by)

        attempt = 1
        while True:
            try:
                items = query.all()
                break
            except Exception as e:
                app.logger.warn("Database Exception in Datastore::get_all_ctype_filtered. "
                                "Sleeping for a few seconds. Attempt {}.".format(attempt))
                app.logger.debug("Exception: {}".format(e))
                import time
                time.sleep(5)
                attempt = attempt + 1
                if attempt > 5:
                    raise Exception("Too many retries for database connections.")

        for item in items:
            if not item.latest_revision_id:
                app.logger.debug("There are no itemrevisions for this item: {}".format(item.id))
                continue
            most_recent = ItemRevision.query.get(item.latest_revision_id)
            if not most_recent.active and not include_inactive:
                continue
            item_map[item] = most_recent

        return item_map

    def get(self, ctype, region, account, name):
        """
        Returns a list of all revisions for the given item.
        """
        item = self._get_item(ctype, region, account, name)
        return item.revisions

    def get_audit_issues(self, ctype, region, account, name):
        """
        Returns a list of ItemAudit objects associated with a given Item.
        """
        item = self._get_item(ctype, region, account, name)
        return item.issues

    def store(self, ctype, region, account, name, active_flag, config, arn=None, new_issues=None, ephemeral=False,
              source_watcher=None):
        """
        Saves an itemrevision.  Create the item if it does not already exist.
        """
        new_issues = new_issues if new_issues else []
        item = self._get_item(ctype, region, account, name)

        if arn:
            duplicate_arns = Item.query.filter(Item.arn == arn).all()
            for duplicate_item in duplicate_arns:
                if duplicate_item.id != item.id:
                    duplicate_item.arn = None
                    app.logger.info("Moving ARN {arn} from {duplicate} to {item}".format(
                        arn=arn,
                        duplicate=duplicate_item.name,
                        item=item.name
                    ))
                    db.session.add(duplicate_item)
                    db.session.commit()

        if arn:
            item.arn = arn

        item.latest_revision_complete_hash = DeepHash(config)[config]
        if source_watcher and source_watcher.honor_ephemerals:
            ephemeral_paths = source_watcher.ephemeral_paths
        else:
            ephemeral_paths = []
        item.latest_revision_durable_hash = durable_hash(config, ephemeral_paths)

        if ephemeral:
            item_revision = item.revisions.first()
            item_revision.config = config
            item_revision.date_last_ephemeral_change = datetime.datetime.utcnow()
        else:
            item_revision = ItemRevision(active=active_flag, config=config)
            item.revisions.append(item_revision)

        # Add new issues
        for new_issue in new_issues:
            nk = "{}/{}".format(new_issue.issue, new_issue.notes)
            if nk not in ["{}/{}".format(old_issue.issue, old_issue.notes) for old_issue in item.issues]:
                item.issues.append(new_issue)
                db.session.add(new_issue)

        # Delete old issues
        for old_issue in item.issues:
            ok = "{}/{}".format(old_issue.issue, old_issue.notes)
            if ok not in ["{}/{}".format(new_issue.issue, new_issue.notes) for new_issue in new_issues]:
                db.session.delete(old_issue)

        db.session.add(item)
        db.session.add(item_revision)
        db.session.commit()

        self._set_latest_revision(item)
        return item

    def _set_latest_revision(self, item):
        latest_revision = item.revisions.first()
        item.latest_revision_id = latest_revision.id
        db.session.add(item)
        db.session.commit()
        #db.session.close()

    def _delete_duplicate_item(self, items):
        """
        Given a list of identical items (account, name, region, technology), delete the duplicate, and return
        the most current item back out.
        :param items:
        :return:
        """
        last_item = items.pop()

        for i in items:
            if last_item.latest_revision_id > i.latest_revision_id:
                db.session.delete(i)
            else:
                db.session.delete(last_item)
                last_item = i

        db.session.commit()
        return last_item

    def _get_item(self, technology, region, account, name):
        """
        Returns the first item with matching parameters.
        Creates item if it doesn't exist.
        """
        account_result = Account.query.filter(Account.name == account).first()
        if not account_result:
            raise Exception("Account with name [{}] not found.".format(account))

        item = Item.query.join((Technology, Item.tech_id == Technology.id)) \
            .join((Account, Item.account_id == Account.id)) \
            .filter(Technology.name == technology) \
            .filter(Account.name == account) \
            .filter(Item.region == region) \
            .filter(Item.name == name) \
            .all()

        if len(item) > 1:
            app.logger.error("[?] Duplicate items have been detected: {a}/{t}/{r}/{n}. Removing duplicate...".format(
                a=account, t=technology, r=region, n=name))
            item = self._delete_duplicate_item(item)
            app.logger.info("[-] Duplicate items removed: {a}/{t}/{r}/{n}...".format(a=account, t=technology,
                                                                                     r=region, n=name))
        elif len(item) == 1:
            item = item[0]
        else:
            item = None

        if not item:
            technology_result = Technology.query.filter(Technology.name == technology).first()
            if not technology_result:
                technology_result = Technology(name=technology)
                db.session.add(technology_result)
                db.session.commit()
                app.logger.info("Creating a new Technology: {} - ID: {}"
                                .format(technology, technology_result.id))
            item = Item(tech_id=technology_result.id, region=region, account_id=account_result.id, name=name)
            db.session.add(item)
            db.session.commit()
            db.session.refresh(item)
        return item


def store_exception(source, location, exception, ttl=None):
    """
    Method to store exceptions in the database.
    :param source:
    :param location:
    :param exception:
    :param ttl:
    :return:
    """
    try:
        app.logger.debug("Logging exception from {} with location: {} to the database.".format(source, location))
        message = str(exception)[:512]

        exception_entry = ExceptionLogs(source=source, ttl=ttl, type=type(exception).__name__,
                                        message=message, stacktrace=traceback.format_exc())
        if location:
            if len(location) == 4:
                item = Item.query.filter(Item.name == location[3]).first()
                if item:
                    exception_entry.item_id = item.id

            if len(location) >= 3:
                exception_entry.region = location[2]

            if len(location) >= 2:
                account = Account.query.filter(Account.name == location[1]).one()
                if account:
                    exception_entry.account_id = account.id

            if len(location) >= 1:
                technology = Technology.query.filter(Technology.name == location[0]).first()
                if not technology:
                    technology = Technology(name=location[0])
                    db.session.add(technology)
                    db.session.commit()
                    db.session.refresh(technology)
                    app.logger.info("Creating a new Technology: {} - ID: {}".format(technology.name, technology.id))
                exception_entry.tech_id = technology.id

        db.session.add(exception_entry)
        db.session.commit()
        app.logger.debug("Completed logging exception to database.")

    except Exception as e:
        app.logger.error("Encountered exception while logging exception to database:")
        app.logger.exception(e)


def clear_old_exceptions():
    exc_list = ExceptionLogs.query.filter(ExceptionLogs.ttl <= datetime.datetime.utcnow()).all()

    for exc in exc_list:
        db.session.delete(exc)

    db.session.commit()


def delete_item_revisions_by_date(start_date, end_date):
    """This will remove all item revisions per the following strategy:
    0. Iterate over every item.
    1. Get a list of all item revisions within the date range provided.
    2. If the revisions on the date selected refers to ALL revisions of a given item, then delete the item outright, and skip to the next item.
    3. Otherwise, get the latest revision for the item before the start date.
    4. Update the item's latest revision ID to that last good revision
    6. Delete the revisions in the date range.
    """
    db = SQLAlchemy(app=app, session_options={"_enable_transaction_accounting": False})  # Override the session options. This will make things MUUUUCH faster!
    whole_items_to_delete = []
    total_revisions_deleted = 0
    whole_items_deleted = 0
    for item in db.session.query(Item).all():
        # Get all the revisions for this item:
        affected_revisions = db.session.query(ItemRevision).join(Item).filter(ItemRevision.item_id == item.id,
                                                                              ItemRevision.date_created >= start_date, ItemRevision.date_created < end_date
                                                                              ).all()
        if not affected_revisions:
            continue

        # How many revisions does this item have?
        total_number_of_revisions = db.session.query(ItemRevision).filter(ItemRevision.item_id == item.id).count()
        if total_number_of_revisions == len(affected_revisions):
            app.logger.info("[+] Marking Item: {} for deletion as all revisions are in the deletion timeframe.".format(item.arn))
            whole_items_to_delete.append(item)

            # Purge the whole items on 100 item batches
            if len(whole_items_to_delete) == 100:
                for item_to_delete in whole_items_to_delete:
                    db.session.delete(item_to_delete)
                db.session.commit()
                app.logger.info("[---] Deleted a batch of 100 items marked for deletion.")
                whole_items_deleted += 100
                whole_items_to_delete = []  # Reset the batch

            continue

        # Add the affected versions to the deletion list:
        affected_revision_ids = set()
        for af in affected_revisions:
            total_revisions_deleted += 1
            affected_revision_ids.add(af.id)
            app.logger.info("[+] Marking Item Revision for Item: {} / {} to be deleted...".format(af.date_created, item.arn))
            db.session.delete(af)

        # Check if the latest revision ID for the item is in the affected revision:
        if item.latest_revision_id in affected_revision_ids:
            # If so, then we need to point the latest revision of the item to the last known good item (before the deletion start date)
            # Get the latest revision that is
            latest_good_revision = db.session.query(ItemRevision).filter(ItemRevision.item_id == item.id,
                                                                         ItemRevision.date_created < start_date
                                                                         ).order_by(desc(ItemRevision.date_created)).first()
            # Update the item to point to the last good revision:
            item.latest_revision_id = latest_good_revision.id
            app.logger.info("[~] The item's latest revision is in the deletion list. "
                            "Updating with the last known good change item: {}.".format(latest_good_revision.date_created))
            db.session.add(item)

        db.session.commit()
        app.logger.info("[-] Deleted {} Item Revisions for Item: {}".format(len(affected_revisions), item.arn))

    # Delete remaining whole items not processed in the 100 batches above:
    for item_to_delete in whole_items_to_delete:
        db.session.delete(item_to_delete)
        whole_items_deleted += 1
    db.session.commit()

    app.logger.info("[-] Deleted {} full items.".format(whole_items_deleted))
    app.logger.info("[-] Deleted {} individual revisions.".format(total_revisions_deleted))
