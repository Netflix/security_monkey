from collections import defaultdict

from six import text_type

from security_monkey.datastore import Account, Technology, Item
from security_monkey.datastore import store_exception, ExceptionLogs
from security_monkey.datastore import clear_old_exceptions, AccountType
from security_monkey import db, ARN_PREFIX
from security_monkey.tests import SecurityMonkeyTestCase

import traceback
import datetime

import random
import string


class ExceptionLoggingTestCase(SecurityMonkeyTestCase):
    def pre_test_setup(self):
        account_type_result = AccountType.query.filter(AccountType.name == 'AWS').first()
        if not account_type_result:
            account_type_result = AccountType(name='AWS')
            db.session.add(account_type_result)
            db.session.commit()

        self.account = Account(identifier="012345678910", name="testing",
                               account_type_id=account_type_result.id)
        self.technology = Technology(name="iamrole")
        self.item = Item(region="us-west-2", name="testrole",
                         arn=ARN_PREFIX + ":iam::012345678910:role/testrole", technology=self.technology,
                         account=self.account)

        db.session.add(self.account)
        db.session.add(self.technology)
        db.session.add(self.item)

        db.session.commit()

    def tearDown(self):
        import security_monkey.auditor
        security_monkey.auditor.auditor_registry = defaultdict(list)
        super(ExceptionLoggingTestCase, self).tearDown()

    def test_doesnt_delete_parent_cascade(self):
        """
        If the exception is deleted, the parent (tech., item, account) should not be deleted.
        :return:
        """
        try:
            raise ValueError("This is a test")
        except ValueError as e:
            test_exception = e

        location = ("iamrole", "testing", "us-west-2", "testrole")
        store_exception("tests", location, test_exception)

        exc = ExceptionLogs.query.all()
        db.session.delete(exc[0])

        db.session.commit()

        assert len(Item.query.filter(Item.name == "testrole").all()) == 1
        assert len(Technology.query.filter(Technology.name == "iamrole").all()) == 1
        assert len(Account.query.filter(Account.name == "testing").all()) == 1

    def test_child_deletion_cascade_check(self):
        """
        If the exception object is deleted, then the parent object (items, account, tech.) should NOT be deleted.
        :return:
        """
        try:
            raise ValueError("This is a test")
        except ValueError as e:
            test_exception = e

        location = ("iamrole", "testing", "us-west-2", "testrole")
        store_exception("tests", location, test_exception)

        assert len(self.item.exceptions) == 1
        assert len(self.account.exceptions) == 1
        assert len(self.technology.exceptions) == 1

        db.session.delete(self.item.exceptions[0])
        db.session.commit()

        exc = ExceptionLogs.query.all()
        assert len(exc) == 0

        assert len(Item.query.filter(Item.name == "testrole").all()) == 1
        assert len(Technology.query.filter(Technology.name == "iamrole").all()) == 1
        assert len(Account.query.filter(Account.name == "testing").all()) == 1

        assert len(self.item.exceptions) == 0
        assert len(self.account.exceptions) == 0
        assert len(self.technology.exceptions) == 0

    def test_safe_child_deletion_cascade(self):
        """
        If the parent is deleted (item, account, tech.), the exception should be deleted, BUT the other parents
        should remain.
        :return:
        """
        try:
            raise ValueError("This is a test")
        except ValueError as e:
            test_exception = e

        location = ("iamrole", "testing", "us-west-2", "testrole")
        store_exception("tests", location, test_exception)

        db.session.delete(self.item)
        db.session.commit()

        exc = ExceptionLogs.query.all()
        assert len(exc) == 0

        assert len(Item.query.filter(Item.name == "testrole").all()) == 0
        assert len(Technology.query.filter(Technology.name == "iamrole").all()) == 1
        assert len(Account.query.filter(Account.name == "testing").all()) == 1

    def test_store_exception(self):
        try:
            raise ValueError("This is a test")
        except ValueError as e:
            test_exception = e

        attrs = [
            ("technology", "iamrole"),
            ("account", "testing"),
            ("region", "us-west-2"),
            ("item", "testrole")
        ]

        location = ("iamrole", "testing", "us-west-2", "testrole")

        ttl_month = (datetime.datetime.utcnow() + datetime.timedelta(days=10)).month
        ttl_day = (datetime.datetime.utcnow() + datetime.timedelta(days=10)).day
        current_month = datetime.datetime.utcnow().month
        current_day = datetime.datetime.utcnow().day

        # Test all cases...
        for i in range(1, 5):
            store_exception("tests", tuple(location[:i]), test_exception)

            # Fetch the exception and validate it:
            exc_log = ExceptionLogs.query.order_by(ExceptionLogs.id.desc()).first()

            assert exc_log.type == type(test_exception).__name__
            assert exc_log.message == str(test_exception)
            assert exc_log.stacktrace == traceback.format_exc()
            assert exc_log.occurred.day == current_day
            assert exc_log.occurred.month == current_month
            assert exc_log.ttl.month == ttl_month
            assert exc_log.ttl.day == ttl_day

            for x in range(0, i):
                attr = getattr(exc_log, attrs[x][0])
                if isinstance(attr, text_type):
                    assert attr == attrs[x][1]
                else:
                    assert attr.name == attrs[x][1]

        assert len(self.account.exceptions) == 3
        assert len(self.technology.exceptions) == 4
        assert len(self.item.exceptions) == 1

    def test_exception_length(self):
        some_string = "".join(random.choice(string.ascii_uppercase) for _ in range(1024))

        try:
            raise ValueError(some_string)
        except ValueError as e:
            test_exception = e

        location = ("iamrole", "testing", "us-west-2", "testrole")

        store_exception("tests", location, test_exception)

        exc_log = ExceptionLogs.query.order_by(ExceptionLogs.id.desc()).first()

        assert len(exc_log.message) == 512
        assert exc_log.message[:512] == some_string[:512]

    def test_exception_clearing(self):
        location = ("iamrole", "testing", "us-west-2", "testrole")

        for i in range(0, 5):
            try:
                raise ValueError("This is test: {}".format(i))
            except ValueError as e:
                test_exception = e

            store_exception("tests", location, test_exception,
                            ttl=(datetime.datetime.now() - datetime.timedelta(days=1)))

        store_exception("tests", location, test_exception)

        clear_old_exceptions()

        # Get all the exceptions:
        exc_list = ExceptionLogs.query.all()

        assert len(exc_list) == 1

    def test_store_exception_with_new_techid(self):
        try:
            raise ValueError("This is a test")
        except ValueError as e:
            test_exception = e

        location = ['newtech']
        ttl_month = (datetime.datetime.utcnow() + datetime.timedelta(days=10)).month
        ttl_day = (datetime.datetime.utcnow() + datetime.timedelta(days=10)).day
        current_month = datetime.datetime.utcnow().month
        current_day = datetime.datetime.utcnow().day

        store_exception("tests", location, test_exception)

        # Fetch the exception and validate it:
        exc_logs = ExceptionLogs.query.all()
        assert len(exc_logs) == 1
        exc_log = exc_logs[0]
        assert exc_log.type == type(test_exception).__name__
        assert exc_log.message == str(test_exception)
        assert exc_log.stacktrace == traceback.format_exc()
        assert exc_log.occurred.day == current_day
        assert exc_log.occurred.month == current_month
        assert exc_log.ttl.month == ttl_month
        assert exc_log.ttl.day == ttl_day

        tech = Technology.query.filter(Technology.name == "newtech").first()
        assert tech
        assert exc_log.tech_id == tech.id
