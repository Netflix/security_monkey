from security_monkey.cloudaux_watcher import CloudAuxWatcher
from cloudaux.aws.elbv2 import describe_load_balancers
from cloudaux.orchestration.aws.elbv2 import get_elbv2


class ELBv2(CloudAuxWatcher):
    index = 'alb'
    i_am_singular = 'ALB'
    i_am_plural = 'ALBs'
    honor_ephemerals = False
    ephemeral_paths = ['_version', 'TargetGroupHealth$*$Target$Id']
    service_name = 'elbv2'

    def get_name_from_list_output(self, item):
        return item['LoadBalancerName']

    def list_method(self, **kwargs):
        return describe_load_balancers(**kwargs)

    def get_method(self, item, **kwargs):
        return get_elbv2(item, **kwargs)
