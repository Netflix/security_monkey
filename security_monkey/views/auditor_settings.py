from security_monkey.views import AuthenticatedService
from security_monkey.views import __check_auth__
from security_monkey.datastore import Account, AuditorSettings, Technology, ItemAudit
from security_monkey.views import AUDITORSETTING_FIELDS
from security_monkey import db

from flask.ext.restful import marshal, reqparse
from sqlalchemy import func


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
                            issue: "User with password login.",
                            count: 15
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

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        self.reqparse.add_argument('accounts', type=str, default=None, location='args')
        self.reqparse.add_argument('technologies', type=str, default=None, location='args')
        self.reqparse.add_argument('enabled', type=bool, default=None, location='args')
        self.reqparse.add_argument('issue', type=str, default=None, location='args')
        self.reqparse.add_argument('order_by', type=str, default=None, location='args')
        self.reqparse.add_argument('order_dir', type=str, default='Desc', location='args')
        args = self.reqparse.parse_args()

        page = args.pop('page', None)
        count = args.pop('count', None)
        for k, v in args.items():
            if not v:
                del args[k]

        query = AuditorSettings.query
        query = query.join((Account, Account.id == AuditorSettings.account_id))
        query = query.join((Technology, Technology.id == AuditorSettings.tech_id))

        if 'accounts' in args:
            accounts = args['accounts'].split(',')
            query = query.filter(Account.name.in_(accounts))

        if 'technologies' in args:
            technologies = args['technologies'].split(',')
            query = query.filter(Technology.name.in_(technologies))

        if 'enabled' in args:
            query = query.filter(AuditorSettings.disabled != bool(args['enabled']))

        if 'issue' in args:
            query = query.filter(AuditorSettings.issue_text == args['issue'])

        if 'order_by' in args:

            if args['order_by'] == 'account' and args['order_dir'] == 'Desc':
                query = query.order_by(Account.name.desc())
            elif args['order_by'] == 'account' and args['order_dir'] == 'Asc':
                query = query.order_by(Account.name.asc())

            elif args['order_by'] == 'technology' and args['order_dir'] == 'Desc':
                query = query.order_by(Technology.name.desc())
            elif args['order_by'] == 'technology' and args['order_dir'] == 'Asc':
                query = query.order_by(Technology.name.asc())

            elif args['order_by'] == 'enabled' and args['order_dir'] == 'Desc':
                query = query.order_by(AuditorSettings.disabled.asc())
            elif args['order_by'] == 'enabled' and args['order_dir'] == 'Asc':
                query = query.order_by(AuditorSettings.disabled.desc())

            elif args['order_by'] == 'issue' and args['order_dir'] == 'Desc':
                query = query.order_by(AuditorSettings.issue_text.desc())
            elif args['order_by'] == 'issue' and args['order_dir'] == 'Asc':
                query = query.order_by(AuditorSettings.issue_text.asc())

            elif args['order_by'] == 'issue_count':
                stmt = db.session.query(
                    ItemAudit.auditor_setting_id,
                    func.count('*').label('setting_count')
                ).group_by(
                    ItemAudit.auditor_setting_id
                ).subquery()

                query = query.join(
                    (stmt, AuditorSettings.id == stmt.c.auditor_setting_id)
                )

                if args['order_dir'] == 'Desc':
                    query = query.order_by(
                        stmt.c.setting_count.desc()
                    )
                elif args['order_dir'] == 'Asc':
                    query = query.order_by(
                        stmt.c.setting_count.asc()
                    )

        enabled_auditors = query.paginate(page, count)

        auditor_settings = []
        for auditor_setting in enabled_auditors.items:
            marshalled = marshal(auditor_setting.__dict__, AUDITORSETTING_FIELDS)
            marshalled = dict(
                marshalled.items() +
                {
                    'account': auditor_setting.account.name,
                    'technology': auditor_setting.technology.name,
                    'count': len(auditor_setting.issues)
                }.items()
            )
            marshalled['issue'] = marshalled['issue_text']
            del marshalled['issue_text']
            auditor_settings.append(marshalled)

        ret_dict = {
            'items': auditor_settings,
            'page': enabled_auditors.page,
            'total': enabled_auditors.total,
            'count': len(auditor_settings),
            'auth': self.auth_dict
        }

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
