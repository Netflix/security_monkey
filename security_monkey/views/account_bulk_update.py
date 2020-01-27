#     Copyright 2017 Bridgewater Associates, LP
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
.. module: security_monkey.views.account_bulk_update
    :platform: Unix
    :synopsis: Updates the active flag for a list of accounts.


.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""


from security_monkey.views import AuthenticatedService
from security_monkey.datastore import Account
from security_monkey import app, db, rbac

from flask import request
from flask_restful import reqparse
import json


class AccountListPut(AuthenticatedService):
    decorators = [
        rbac.allow(["Admin"], ["PUT"])
    ]

    def __init__(self):
        super(AccountListPut, self).__init__()
        self.reqparse = reqparse.RequestParser()

    def put(self):
        values = json.loads(request.json)
        app.logger.debug("Account bulk update {}".format(values))
        for account_name in list(values.keys()):
            account = Account.query.filter(Account.name == account_name).first()
            if account:
                account.active = values[account_name]
                db.session.add(account)

        db.session.commit()
        db.session.close()

        return {'status': 'updated'}, 200
