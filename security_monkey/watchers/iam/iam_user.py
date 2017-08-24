from security_monkey.cloudaux_watcher import CloudAuxWatcher
from security_monkey import AWS_DEFAULT_REGION
from cloudaux.aws.iam import list_users
from cloudaux.orchestration.aws.iam.user import get_user


class IAMUser(CloudAuxWatcher):
    index = 'iamuser'
    i_am_singular = 'IAM User'
    i_am_plural = 'IAM Users'

    def __init__(self, *args, **kwargs):
        super(IAMUser, self).__init__(*args, **kwargs)
        self.honor_ephemerals = True
        self.ephemeral_paths = [
            "PasswordLastUsed",
            "AccessKeys$*$LastUsedDate",
            "AccessKeys$*$Region",
            "AccessKeys$*$ServiceName",
            "_version"]
        self.override_region = 'universal'

    def get_name_from_list_output(self, item):
        return item['UserName']

    def _get_regions(self):
        return [AWS_DEFAULT_REGION]

    def list_method(self, **kwargs):
        return list_users(**kwargs)

    def get_method(self, item, **kwargs):
        return get_user(item, **kwargs)
