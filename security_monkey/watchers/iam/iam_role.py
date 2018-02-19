from security_monkey.cloudaux_batched_watcher import CloudAuxBatchedWatcher
from cloudaux.aws.iam import list_roles
from cloudaux.orchestration.aws.iam.role import get_role
from security_monkey import AWS_DEFAULT_REGION


class IAMRole(CloudAuxBatchedWatcher):
    index = 'iamrole'
    i_am_singular = 'IAM Role'
    i_am_plural = 'IAM Roles'
    override_region = 'universal'

    def __init__(self, **kwargs):
        super(IAMRole, self).__init__(**kwargs)
        self.honor_ephemerals = True
        self.ephemeral_paths = ['_version', "Region"]

    def _get_regions(self):
        return [AWS_DEFAULT_REGION]
    
    def get_name_from_list_output(self, item):
        return item['RoleName']

    def list_method(self, **kwargs):
        all_roles = list_roles(**kwargs)
        items = []

        for role in all_roles:
            role["Region"] = "us-east-1"  # IAM is global
            items.append(role)

        return items

    def get_method(self, item, **kwargs):
        # This is not needed for IAM Role:
        item.pop("Region")

        return get_role(dict(item), **kwargs)
