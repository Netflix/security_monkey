from security_monkey.views import AuthenticatedService
from security_monkey.views import __check_auth__
from security_monkey.datastore import Account, Item, ItemAudit, AuditorSettings, Technology
from security_monkey import db, app
from security_monkey import api

from flask.ext.restful import marshal, reqparse
from sqlalchemy import and_

class AuditorSettingsGet(AuthenticatedService):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        super(AuditorSettingsGet, self).__init__()

    def get(self):
        """
            .. http:get:: /api/1/auditorsettings

            Get a list of AuditorSetting items

            **Example Request**:

            .. sourcecode:: http

                GET /api/1/auditorsettings HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Content-Type: application/json

                {
                    count: 15,
                    items: [
                        {
                            id: 1,
                            account: "aws-account-name",
                            technology: "iamuser",
                            disabled: true,
                            issue: "User with password login."
                        },
                        ...
                    ]
                    auth: {
                        authenticated: true,
                        user: "user@example.com"
                    }
                }

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.


        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        results = AuditorSettings.query.all()

        auditor_settings = []
        for auditor_setting in results: 
            issue_count = ItemAudit.query.join(Item).filter(and_(Item.tech_id == auditor_setting.tech_id,
                                                           Item.account_id == auditor_setting.account_id,
                                                           ItemAudit.issue == auditor_setting.issue)).count()
            account = Account.query.filter(Account.id == auditor_setting.account_id).first().name
            technology = Technology.query.filter(Technology.id == auditor_setting.tech_id).first().name
            auditor_settings.append({'account': account,
                                     'technology': technology,
                                     'issue': auditor_setting.issue,
                                     'count': issue_count,
                                     'disabled': auditor_setting.disabled,
                                     'id': auditor_setting.id})
        ret_dict = {}
        ret_dict['items'] = auditor_settings
        ret_dict['count'] = len(auditor_settings)
        ret_dict['auth'] = self.auth_dict

        return ret_dict, 200

class AuditorSettingsPut(AuthenticatedService):
    def __init__(self):
            self.reqparse = reqparse.RequestParser()
            super(AuditorSettingsPut, self).__init__()
    
    def put(self, as_id):
        """
            .. http:put:: /api/1/auditorsettings/<int ID>

            Update an AuditorSetting

            **Example Request**:

            .. sourcecode:: http

                PUT /api/1/auditorsettings/1 HTTP/1.1
                Host: example.com
                Accept: application/json, text/javascript

                {
                    account: "aws-account-name",
                    disabled: false,
                    id: 1,
                    issue: "User with password login.",
                    technology: "iamuser"
                }


            **Example Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Content-Type: application/json

            :statuscode 200: no error
            :statuscode 401: Authentication failure. Please login.
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('disabled', type=bool, required=True, location='json')
        args = self.reqparse.parse_args()
        disabled = args.pop('disabled', None)
        results = AuditorSettings.query.get(as_id)
        results.disabled = disabled
        db.session.add(results)
        db.session.commit()
        return 200
