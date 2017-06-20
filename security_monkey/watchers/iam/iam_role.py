from security_monkey.cloudaux_batched_watcher import CloudAuxBatchedWatcher
from cloudaux.aws.iam import list_roles
from cloudaux.orchestration.aws.iam.role import get_role


class IAMRole(CloudAuxBatchedWatcher):
    index = 'iamrole'
    i_am_singular = 'IAM Role'
    i_am_plural = 'IAM Roles'
    honor_ephemerals = False
    ephemeral_paths = ['_version']
    override_region = 'universal'

    def __init__(self, **kwargs):
        super(IAMRole, self).__init__(**kwargs)

    def _get_regions(self):
        return ['us-east-1']
    
    def get_name_from_list_output(self, item):
        return item['RoleName']

    def list_method(self, **kwargs):
        return list_roles(**kwargs)

    def get_method(self, item, **kwargs):
        return get_role(dict(item), **kwargs)
