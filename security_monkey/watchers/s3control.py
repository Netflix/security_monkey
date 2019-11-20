import boto3
from security_monkey.common.sts_connect import connect
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app

from dumper import dump

class S3Control(Watcher):
    index = 's3control'
    i_am_singular = 'S3 Control'
    i_am_plural = 'S3 Controls'
    override_region = 'universal'

    def __init__(self, accounts=None, debug=False):
        super(S3Control, self).__init__(accounts=accounts, debug=debug)
        self.honor_ephemerals = True
        self.service_name = 's3control'

    def slurp(self):
        self.prep_for_slurp()

        item_list = []
        exception_map = {}

        for account in self.accounts:
            try:
                s3client = connect(account, 'boto3.s3control.client')

                castleblack = self.wrap_aws_rate_limited_call(
                    s3client.get_public_access_block, AccountId = self.account_identifiers[0]
                )
                item_config = {
                        "PublicAccessBlock": castleblack['PublicAccessBlockConfiguration']
                }
                item = S3ControlItem(account=account, name='S3 Control {}'.format(self.account_identifiers[0]), config=item_config, source_watcher=self)
                item_list.append(item)

            except Exception as e:
                dump(str(e))
                exc = BotoConnectionIssue(str(e), 's3control', account, None)
                self.slurp_exception((self.index, account, 'universal'), exc, exception_map, source="{}-watcher".format(self.index))
                continue

        return item_list, exception_map


class S3ControlItem(ChangeItem):
    def __init__(self, account=None, name=None, arn=None, config=None, source_watcher=None):
        super(S3ControlItem, self).__init__(
            index=S3Control.index,
            region='universal',
            account=account,
            name=name,
            arn=arn,
            new_config=config if config else {},
            source_watcher=source_watcher)

