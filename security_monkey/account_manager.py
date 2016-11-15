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
from datastore import Account, AccountType, AccountTypeCustomValues
from security_monkey import app, db
from security_monkey.common.utils import find_modules

account_registry = {}


class AccountManagerType(type):
    """
    Generates a global account regstry as AccountManager derived classes
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

    def __init__(self, name, label, db_item, tool_tip, password=False):
        super(CustomFieldConfig, self).__init__()
        self.name = name
        self.label = label
        self.db_item = db_item
        self.tool_tip = tool_tip
        self.password = password


class AccountManager(object):
    __metaclass__ = AccountManagerType
    account_type = None
    compatable_account_types = []
    custom_field_configs = []
    identifier_label = None
    identifier_tool_tip = None

    def update(self, account_id, account_type, name, active, third_party, notes,
               identifier, custom_fields=None):
        """
        Updates an existing account in the database.
        """
        account_type_result = _get_or_create_account_type(account_type)
        query = Account.query.filter(Account.id == account_id)
        if query.count():
            account = query.first()
        else:
            app.logger.info(
                'Account with id {} does not exist exists'.format(account_id))
            return None

        account = self._populate_account(account, account_type_result.id, name,
                                         active, third_party, notes, identifier, custom_fields)

        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        account = self._load(account)
        return account

    def create(self, account_type, name, active, third_party, notes, identifier,
               custom_fields=None):
        """
        Creates an account in the database.
        """
        account_type_result = _get_or_create_account_type(account_type)
        account = Account()
        account = self._populate_account(account, account_type_result.id, name,
                                         active, third_party, notes, identifier, custom_fields)

        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        account = self._load(account)
        return account

    def lookup_account_by_identifier(self, identifier):
        query = Account.query.filter(Account.identifier == identifier)

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
        account.name = name
        account.identifier = identifier
        account.notes = notes
        account.active = active
        account.third_party = third_party
        account.account_type_id = account_type_id
        if account.custom_fields is None:
            account.custom_fields = []

        for custom_config in self.custom_field_configs:
            if custom_config.db_item:
                field_name = custom_config.name
                for current_field in account.custom_fields:
                    if current_field.name == field_name:
                        if current_field.value != custom_fields.get(field_name):
                            current_field.value = custom_fields.get(field_name)
                            db.session.add(current_field)
                        break
                else:
                    new_value = AccountTypeCustomValues(
                        name=field_name, value=custom_fields.get(field_name))
                    account.custom_fields.append(new_value)

        return account

    def is_compatible_with_account_type(self, account_type):
        if self.account_type == account_type or account_type in self.compatable_account_types:
            return True
        return False


def load_all_account_types():
    """ Verifies all account types are in the database """
    for account_type in account_registry.keys():
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

find_modules('account_managers')
