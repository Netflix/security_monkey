from security_monkey.cloudaux_watcher import CloudAuxWatcher
from cloudaux.aws.elbv2 import describe_load_balancers
from cloudaux.orchestration.aws.elbv2 import get_elbv2


class ELBv2(CloudAuxWatcher):
    index = 'alb'
    i_am_singular = 'ALB'
    i_am_plural = 'ALBs'
    service_name = 'elbv2'

    def __init__(self, accounts=None, debug=None):
        super(ELBv2, self).__init__(accounts=accounts, debug=debug)

        self.honor_ephemerals = True
        self.ephemeral_paths = ['_version', 'TargetGroupHealth']

    def get_name_from_list_output(self, item):
        return item['LoadBalancerName']

    def list_method(self, **kwargs):
        return describe_load_balancers(**kwargs)

    def get_method(self, item, **kwargs):
        return get_elbv2(item, **kwargs)
