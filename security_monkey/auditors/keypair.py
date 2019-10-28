from security_monkey.auditor import Auditor, Categories
from security_monkey.watchers.keypair import Keypair


class KeypairAuditor(Auditor):
    index = Keypair.index
    i_am_singular = Keypair.i_am_singular
    i_am_plural = Keypair.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(KeypairAuditor, self).__init__(accounts=accounts, debug=debug)

    def check_keypair_assignment(self, item):
        if not len(item.config.get('instances', [])):
            self.add_issue(0, Categories.CANDIDATE_FOR_DELETION, item, notes="Keypair not used for any instances")
