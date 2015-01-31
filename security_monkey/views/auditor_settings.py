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
        TODO qlo: Notes about API usage here
        """
        auth, retval = __check_auth__(self.auth_dict)
        if auth:
            return retval

        self.reqparse.add_argument('count', type=int, default=30, location='args')
        self.reqparse.add_argument('page', type=int, default=1, location='args')
        args = self.reqparse.parse_args()
        # TODO qlo: Actually respect page/count
        page = args.pop('page', None)
        count = args.pop('count', None)

        results = AuditorSettings.query.all()
        
        auditor_settings = []
        for auditor_setting in results: 
            issue_count = ItemAudit.query.join(Item).filter(and_(Item.tech_id == auditor_setting.tech_id, 
                                                           Item.account_id == auditor_setting.account_id, 
                                                           ItemAudit.issue == auditor_setting.issue)).count()
            account_name = Account.query.filter(Account.id == auditor_setting.account_id).first().name
            tech_name = Technology.query.filter(Technology.id == auditor_setting.tech_id).first().name
            auditor_settings.append({'account_name': account_name,
                                     'tech_name': tech_name,
                                     'issue': auditor_setting.issue,
                                     'count': issue_count,
                                     'disabled': auditor_setting.disabled,
                                     'id': auditor_setting.id})
        ret_dict = {}
        ret_dict['items'] = auditor_settings
        ret_dict['count'] = len(auditor_settings)
        ret_dict['auth'] = self.auth_dict
        ret_dict['page'] = page
        ret_dict['total'] = len(auditor_settings)
        return ret_dict, 200

class AuditorSettingsPut(AuthenticatedService):
    """
    TODO qlo: Notes about API usage here
    """
    def __init__(self):
            self.reqparse = reqparse.RequestParser()
            super(AuditorSettingsPut, self).__init__()
    
    def put(self, as_id):
        app.logger.debug("Put")
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
