#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.account
    :platform: Unix
    :synopsis: Base class for aws and other custom account types.


.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>

"""
from .datastore import Account, AccountType, AccountTypeCustomValues, User
from security_monkey import app, db
from security_monkey.common.utils import find_modules
import psycopg2
import traceback

from security_monkey.exceptions import AccountNameExists

account_registry = {}


class AccountManagerType(type):
    """
    Generates a global account registry as AccountManager derived classes
    are loaded
    """
    def __init__(cls, name, bases, attrs):
        super(AccountManagerType, cls).__init__(name, bases, attrs)
        if cls.account_type:
            app.logger.info("Registering account %s %s",
                            cls.account_type, cls.__name__)
            account_registry[cls.account_type] = cls


class CustomFieldConfig(object):
    """
    Defines additional field types for custom account types
    """

    def __init__(self, name, label, db_item, tool_tip, password=False, allowed_values=None):
        super(CustomFieldConfig, self).__init__()
        self.name = name
        self.label = label
        self.db_item = db_item
        self.tool_tip = tool_tip
        self.password = password
        self.allowed_values = allowed_values


class AccountManager(object, metaclass=AccountManagerType):
    account_type = None
    compatable_account_types = []
    custom_field_configs = []
    identifier_label = None
    identifier_tool_tip = None

    def sanitize_account_identifier(self, identifier):
        """Each account type can determine how to sanitize the account identifier.
        By default, will strip any whitespace.

        Returns:
            identifier stripped of whitespace
        """
        return identifier.strip()

    def sanitize_account_name(self, name):
        """Each account type can determine how to sanitize the account name.
        By default, will strip trailing whitespace.
        Account alias (name) can have spaces and special characters

        Returns:
            name stripped of ending whitespace
        """
        return name.rstrip()

    def sync(self, account_type, name, active, third_party, notes, identifier, custom_fields):
        """
        Syncs the account with the database. If account does not exist it is created. Other attributes
        including account name are updated to conform with the third-party data source.
        """
        account_type_result = _get_or_create_account_type(account_type)

        account = Account.query.filter(Account.identifier == identifier).first()

        if not account:
            account = Account()

        account = self._populate_account(account, account_type_result.id, self.sanitize_account_name(name),
                                         active, third_party, notes,
                                         self.sanitize_account_identifier(identifier),
                                         custom_fields)

        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        account = self._load(account)
        db.session.expunge(account)
        return account

    def update(self, account_id, account_type, name, active, third_party, notes, identifier, custom_fields=None):
        """
        Updates an existing account in the database.
        """
        _get_or_create_account_type(account_type)

        # Query the account by ID if provided:
        if account_id:
            account = Account.query.filter(Account.id == account_id).first()

            if not account:
                app.logger.error("Account with ID {} does not exist.".format(account_id))
                return None

            # Are we changing the account name?
            if account.name != name:
                # Check if the account with that name exists:
                if Account.query.filter(Account.name == name).first():
                    app.logger.error("Account with name: {} already exists.".format(name))
                    raise AccountNameExists(name)

                account.name = self.sanitize_account_name(name)

        else:
            account = Account.query.filter(Account.name == name).first()
            if not account:
                app.logger.error("Account with name {} does not exist.".format(name))
                return None

        account.active = active
        account.notes = notes
        account.active = active
        account.third_party = third_party
        account.identifier = self.sanitize_account_identifier(identifier)
        self._update_custom_fields(account, custom_fields)

        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        account = self._load(account)
        db.session.expunge(account)
        return account

    def create(self, account_type, name, active, third_party, notes, identifier,
               custom_fields=None):
        """
        Creates an account in the database.
        """
        account_type_result = _get_or_create_account_type(account_type)
        account = Account.query.filter(
            Account.name == name,
            Account.account_type_id == account_type_result.id).first()

        # Make sure the account doesn't already exist:
        if account:
            app.logger.error(
                'Account with name {} already exists!'.format(name))
            return None

        account = Account()
        account = self._populate_account(account, account_type_result.id, self.sanitize_account_name(name),
                                         active, third_party, notes,
                                         self.sanitize_account_identifier(identifier),
                                         custom_fields)

        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        account = self._load(account)
        return account

    def lookup_account_by_identifier(self, identifier):
        query = Account.query.filter(
            Account.identifier == self.sanitize_account_identifier(identifier))

        if query.count():
            return query.first()
        else:
            return None

    def _load(self, account):
        """
        Placeholder for additional load related processing to be implemented
        by account type specific subclasses
        """
        return account

    def _populate_account(self, account, account_type_id, name, active, third_party,
                          notes, identifier, custom_fields=None):
        """
        Creates account DB object to be stored in the DB by create or update.
        May be overridden to store additional data
        """
        account.name = self.sanitize_account_name(name)
        account.identifier = self.sanitize_account_identifier(identifier)
        account.notes = notes
        account.active = active
        account.third_party = third_party
        account.account_type_id = account_type_id

        self._update_custom_fields(account, custom_fields)

        return account

    def _update_custom_fields(self, account, provided_custom_fields):
        existing_values = {}

        if account.custom_fields is None:
            account.custom_fields = []

        for cf in account.custom_fields:
            existing_values[cf.name] = cf

        for custom_config in self.custom_field_configs:
            if custom_config.db_item:
                # The default value for a field that is not present and without any value set is `None`.
                new_value = None

                try:
                    # Is this field passed in? If not...
                    if not provided_custom_fields.get(custom_config.name):
                        # Does this field already exist for the account?
                        # If it doesn't, then this will create a new empty field. Otherwise, do nothing.
                        _ = existing_values[custom_config.name]

                    else:
                        # Need to check if this field is new for the account -- or updating an existing value.
                        new_value = provided_custom_fields[custom_config.name]
                        if existing_values[custom_config.name].value != new_value:
                            # There is a change, so update:
                            existing_values[custom_config.name].value = new_value
                            db.session.add(existing_values[custom_config.name])

                except KeyError:
                    # The field does not exist, so add it with the correct value:
                    new_custom_value = AccountTypeCustomValues(name=custom_config.name, value=new_value)
                    account.custom_fields.append(new_custom_value)
                    db.session.add(account)

    def is_compatible_with_account_type(self, account_type):
        if self.account_type == account_type or account_type in self.compatable_account_types:
            return True
        return False


def load_all_account_types():
    """ Verifies all account types are in the database """
    for account_type in list(account_registry.keys()):
        _get_or_create_account_type(account_type)


def _get_or_create_account_type(account_type):
    account_type_result = AccountType.query.filter(
        AccountType.name == account_type).first()
    if not account_type_result:
        account_type_result = AccountType(name=account_type)
        db.session.add(account_type_result)
        db.session.commit()
        app.logger.info("Creating a new AccountType: {} - ID: {}"
                        .format(account_type, account_type_result.id))

    return account_type_result


def get_account_by_id(account_id):
    """
    Retrieves an account plus any additional custom fields
    """
    account = Account.query.filter(Account.id == account_id).first()
    manager_class = account_registry.get(account.account_type.name)
    account = manager_class()._load(account)
    db.session.expunge(account)
    return account


def get_account_by_name(account_name):
    """
    Retrieves an account plus any additional custom fields
    """
    account = Account.query.filter(Account.name == account_name).first()
    manager_class = account_registry.get(account.account_type.name)
    account = manager_class()._load(account)
    db.session.expunge(account)
    return account


def delete_account_by_id(account_id):

    # Need to unsubscribe any users first:
    users = User.query.filter(
        User.accounts.any(Account.id == account_id)).all()
    for user in users:
        user.accounts = [
            account for account in user.accounts if not account.id == account_id]
        db.session.add(user)
        db.session.commit()

    conn = None
    try:
        # The SQL Alchemy method of handling cascading deletes is inefficient.
        # As a result, deleting accounts with large numbers of items and issues
        # can result is a very lengthy service call that time out. This section
        # deletes issues, items and associated child rows using database
        # optimized queries, which results in much faster performance
        conn = psycopg2.connect(app.config.get('SQLALCHEMY_DATABASE_URI'))
        cur = conn.cursor()
        cur.execute('DELETE from issue_item_association '
                    'WHERE super_issue_id IN '
                    '(SELECT itemaudit.id from itemaudit, item '
                    'WHERE itemaudit.item_id = item.id AND item.account_id = %s);', [account_id])

        cur.execute('DELETE from itemaudit WHERE item_id IN '
                    '(SELECT id from item WHERE account_id = %s);', [account_id])

        cur.execute('DELETE from itemrevisioncomment WHERE revision_id IN '
                    '(SELECT itemrevision.id from itemrevision, item WHERE '
                    'itemrevision.item_id = item.id AND item.account_id = %s);', [account_id])

        cur.execute('DELETE from cloudtrail WHERE revision_id IN '
                    '(SELECT itemrevision.id from itemrevision, item WHERE '
                    'itemrevision.item_id = item.id AND item.account_id = %s);', [account_id])

        cur.execute('DELETE from itemrevision WHERE item_id IN '
                    '(SELECT id from item WHERE account_id = %s);', [account_id])

        cur.execute('DELETE from itemcomment WHERE item_id IN '
                    '(SELECT id from item WHERE account_id = %s);', [account_id])

        cur.execute('DELETE from exceptions WHERE item_id IN '
                    '(SELECT id from item WHERE account_id = %s);', [account_id])

        cur.execute('DELETE from cloudtrail WHERE item_id IN '
                    '(SELECT id from item WHERE account_id = %s);', [account_id])

        cur.execute('DELETE from item WHERE account_id = %s;', [account_id])

        cur.execute('DELETE from exceptions WHERE account_id = %s;', [account_id])

        cur.execute('DELETE from auditorsettings WHERE account_id = %s;', [account_id])

        cur.execute('DELETE from account_type_values WHERE account_id = %s;', [account_id])

        cur.execute('DELETE from account WHERE id = %s;', [account_id])

        conn.commit()
    except Exception as e:
        app.logger.warn(traceback.format_exc())
    finally:
        if conn:
            conn.close()


def delete_account_by_name(name):
    account = Account.query.filter(Account.name == name).first()
    account_id = account.id
    db.session.expunge(account)
    delete_account_by_id(account_id)


def bulk_disable_accounts(account_names):
    """Bulk disable accounts"""
    for account_name in account_names:
        account = Account.query.filter(Account.name == account_name).first()
        if account:
            app.logger.debug("Disabling account %s", account.name)
            account.active = False
            db.session.add(account)

    db.session.commit()
    db.session.close()


def bulk_enable_accounts(account_names):
    """Bulk enable accounts"""
    for account_name in account_names:
        account = Account.query.filter(Account.name == account_name).first()
        if account:
            app.logger.debug("Enabling account %s", account.name)
            account.active = True
            db.session.add(account)

    db.session.commit()
    db.session.close()


find_modules('account_managers')
