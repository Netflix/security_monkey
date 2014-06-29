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


from security_monkey import db, app

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Unicode
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship
from flask.ext.security import UserMixin, RoleMixin

import datetime


association_table = db.Table('association',
                             Column('user_id', Integer, ForeignKey('user.id')),
                             Column('account_id', Integer, ForeignKey('account.id'))
)


class Account(db.Model):
    """
    Meant to model AWS accounts.
    """
    __tablename__ = "account"
    id = Column(Integer, primary_key=True)
    active = Column(Boolean())
    third_party = Column(Boolean())
    name = Column(String(32))
    notes = Column(String(256))
    s3_name = Column(String(32))
    number = Column(String(12))  # Not stored as INT because of potential leading-zeros.
    items = relationship("Item", backref="account")


class Technology(db.Model):
    """
    meant to model AWS primatives (elb, s3, iamuser, iamgroup, etc.)
    """ 
    __tablename__ = 'technology'
    id = Column(Integer, primary_key=True)
    name = Column(String(32))  # elb, s3, iamuser, iamgroup, etc.
    items = relationship("Item", backref="technology")


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    """
    Currently unused.  Will soon have roles for limited users and
    admin users.
    """
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    

class User(db.Model, UserMixin):
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
    accounts = relationship("Account", secondary=association_table)
    item_audits = relationship("ItemAudit", uselist=False, backref="user")
    revision_comments = relationship("ItemRevisionComment", backref="user")
    item_comments = relationship("ItemComment", backref="user")
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)


class ItemAudit(db.Model):
    """
    Meant to model an issue attached to a single item.
    """
    __tablename__ = "itemaudit"
    id = Column(Integer, primary_key=True)
    score = Column(Integer)
    issue = Column(String(512))
    notes = Column(String(512))
    justified = Column(Boolean)
    justified_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    justification = Column(String(512))
    justified_date = Column(DateTime(), default=datetime.datetime.utcnow, nullable=True)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)


class Item(db.Model):
    """
    Meant to model a specific item, like an instance of a security group.
    """
    __tablename__ = "item"
    id = Column(Integer, primary_key=True)
    cloud = Column(String(32))  # AWS, Google, Other
    region = Column(String(32))
    name = Column(String(128))
    tech_id = Column(Integer, ForeignKey("technology.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    revisions = relationship("ItemRevision", backref="item", cascade="all, delete, delete-orphan", order_by="desc(ItemRevision.date_created)")
    issues = relationship("ItemAudit", backref="item", cascade="all, delete, delete-orphan")
    latest_revision_id = Column(Integer, nullable=True)
    comments = relationship("ItemComment", backref="revision", cascade="all, delete, delete-orphan", order_by="ItemComment.date_created")


class ItemComment(db.Model):
    """
    The Web UI allows users to add comments to items.
    """
    __tablename__ = "itemcomment"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('item.id'), nullable=False)
    date_created = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False)
    text = Column(Unicode(1024))


class ItemRevision(db.Model):
    """
    Every new configuration for an item is saved in a new ItemRevision.
    """
    __tablename__ = "itemrevision"
    id = Column(Integer, primary_key=True)
    active = Column(Boolean())
    config = Column(JSON)
    date_created = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False)
    item_id = Column(Integer, ForeignKey("item.id"), nullable=False)
    comments = relationship("ItemRevisionComment", backref="revision", cascade="all, delete, delete-orphan", order_by="ItemRevisionComment.date_created")


class ItemRevisionComment(db.Model):
    """
    The Web UI allows users to add comments to revisions.
    """
    __tablename__ = "itemrevisioncomment"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    revision_id = Column(Integer, ForeignKey('itemrevision.id'), nullable=False)
    date_created = Column(DateTime(), default=datetime.datetime.utcnow, nullable=False)
    text = Column(Unicode(1024))


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
        for k, v in filter_by.items():
            if not v:
                del filter_by[k]

        query = query.filter_by(**filter_by)

        attempt = 1
        while True:
            try:
                items = query.all()
                break
            except Exception as e:
                app.logger.warn("Database Exception in Datastore::get_all_ctype_filtered. Sleeping for a few seconds. Attempt {}.".format(attempt))
                app.logger.debug("Exception: {}".format(e))
                import time
                time.sleep(5)
                attempt = attempt + 1

        for item in items:
            if len(item.revisions) == 0:
                app.logger.debug("There are no itemrevisions for this item: {}".format(item.id))
                continue
            most_recent = item.revisions[0]
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

    def store(self, ctype, region, account, name, active_flag, config, new_issues=[]):
        """
        Saves an itemrevision.  Create the item if it does not already exist.
        """
        item = self._get_item(ctype, region, account, name)
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

    def _set_latest_revision(self, item):
        sorted_revisions = sorted(item.revisions, key=lambda revision: revision.date_created)
        latest_revision = sorted_revisions[-1]
        item.latest_revision_id = latest_revision.id
        db.session.add(item)
        db.session.commit()
        #db.session.close()

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
            # DB needs to be cleaned up and a bug needs to be found if this ever happens.
            raise Exception("Found multiple items for tech: {} region: {} account: {} and name: {}"
                            .format(technology, region, account, name))
        if len(item) == 1:
            item = item[0]
        else:
            item = None

        if not item:
            technology_result = Technology.query.filter(Technology.name == technology).first()
            if not technology_result:
                technology_result = Technology(name=technology)
                db.session.add(technology_result)
                db.session.commit()
                #db.session.close()
                app.logger.info("Creating a new Technology: {} - ID: {}"
                                .format(technology, technology_result.id))
            item = Item(tech_id=technology_result.id, region=region, account_id=account_result.id, name=name)
        return item
