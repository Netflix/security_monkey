from security_monkey.auditor import Auditor, Categories
from security_monkey.watchers.elastic_ip import ElasticIP


class ElasticIPAuditor(Auditor):
    index = ElasticIP.index
    i_am_singular = ElasticIP.i_am_singular
    i_am_plural = ElasticIP.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(ElasticIPAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_if_eip_assigned(self, item):
        if item.config.get('network_interface_id', None) is None:
            self.add_issue(0, Categories.CANDIDATE_FOR_DELETION, item, notes="EIP is not associated with an ENI")
