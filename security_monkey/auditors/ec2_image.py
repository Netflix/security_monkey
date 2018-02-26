from security_monkey.auditor import Auditor, Entity
from security_monkey.watchers.ec2.ec2_image import EC2Image


class EC2ImageAuditor(Auditor):
    index = EC2Image.index
    i_am_singular = EC2Image.i_am_singular
    i_am_plural = EC2Image.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(EC2ImageAuditor, self).__init__(accounts=accounts, debug=debug)

    def prep_for_audit(self):
        super(EC2ImageAuditor, self).prep_for_audit()
        self.FRIENDLY = {account['identifier']: account['name']
                         for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'] if account['label'] == 'friendly'}
        self.THIRDPARTY = {account['identifier']: account['name'] for account in
                           self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'] if account['label'] == 'thirdparty'}

    def check_internet_accessible(self, item):
        accounts = {lp.get('UserId', lp.get('Group')) for lp in item.config.get('LaunchPermissions', [])}
        if 'all' in accounts or item.config.get('Public') == True:
            entity = Entity(category='account', value='all')
            self.record_internet_access(item, entity, actions=['LaunchPermissions'])

    def check_friendly_cross_account(self, item):
        accounts = {lp.get('UserId', lp.get('Group')) for lp in item.config.get('LaunchPermissions', [])}
        for account in accounts:
            if account == 'all':
                continue

            if account in self.FRIENDLY:
                entity = Entity(
                    category='account',
                    value=account,
                    account_name=self.FRIENDLY[account],
                    account_identifier=account)
                self.record_friendly_access(item, entity, actions=['LaunchPermissions'])

    def check_thirdparty_cross_account(self, item):
        accounts = {lp.get('UserId', lp.get('Group')) for lp in item.config.get('LaunchPermissions', [])}
        for account in accounts:
            if account == 'all':
                continue

            if account in self.THIRDPARTY:
                entity = Entity(
                    category='account',
                    value=account,
                    account_name=self.THIRDPARTY[account],
                    account_identifier=account)
                self.record_thirdparty_access(item, entity, actions=['LaunchPermissions'])

    def check_unknown_cross_account(self, item):
        accounts = {lp.get('UserId', lp.get('Group')) for lp in item.config.get('LaunchPermissions', [])}
        for account in accounts:
            if account == 'all':
                continue

            if account not in self.FRIENDLY and account not in self.THIRDPARTY:
                entity = Entity(
                    category='account',
                    value=account)
                self.record_unknown_access(item, entity, actions=['LaunchPermissions'])
