from security_monkey.auditor import Auditor, Categories
from security_monkey.watchers.s3control import S3Control


class S3ControlAuditor(Auditor):
    index = S3Control.index
    i_am_singular = S3Control.i_am_singular
    i_am_plural = S3Control.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(S3ControlAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_castleblack(self, item):
        cb = item.config.get('PublicAccessBlock', None)
        if cb is None or not (cb['IgnorePublicAcls'] and cb['BlockPublicPolicy'] and cb['BlockPublicAcls'] and cb['RestrictPublicBuckets']):
            self.add_issue(10, Categories.INSECURE_CONFIGURATION, item, notes="Account Public Access Block allows public object access")

