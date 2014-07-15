#     Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
.. module: security_monkey.watchers.keypair
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey.constants import IGNORE_PREFIX
from security_monkey import app


class Keypair(Watcher):
  index = 'keypair'
  i_am_singular = 'Keypair'
  i_am_plural = 'Keypairs'

  def __init__(self, accounts=None, debug=False):
    super(Keypair, self).__init__(accounts=accounts, debug=debug)

  def slurp(self):
    """
    :returns: item_list - list of IAM SSH Keypairs.
    :returns: exception_map - A dict where the keys are a tuple containing the
        location of the exception and the value is the actual exception

    """
    item_list = []
    exception_map = {}
    from security_monkey.common.sts_connect import connect
    for account in self.accounts:
      try:
        ec2 = connect(account, 'ec2')
        regions = ec2.get_all_regions()
      except Exception as e:  # EC2ResponseError
        # Some Accounts don't subscribe to EC2 and will throw an exception here.
        exc = BotoConnectionIssue(str(e), 'keypair', account, None)
        self.slurp_exception((self.index, account), exc, exception_map)
        continue

      for region in regions:
        app.logger.debug("Checking {}/{}/{}".format(Keypair.index, account, region.name))

        try:
          rec2 = connect(account, 'ec2', region=region)
          kps = self.wrap_aws_rate_limited_call(
            rec2.get_all_key_pairs
          )
        except Exception as e:
          if region.name not in TROUBLE_REGIONS:
            exc = BotoConnectionIssue(str(e), 'keypair', account, region.name)
            self.slurp_exception((self.index, account, region.name), exc, exception_map)
          continue

        app.logger.debug("Found {} {}".format(len(kps), Keypair.i_am_plural))
        for kp in kps:

          ### Check if this Keypair is on the Ignore List ###
          ignore_item = False
          for ignore_item_name in IGNORE_PREFIX[self.index]:
            if kp.name.lower().startswith(ignore_item_name.lower()):
              ignore_item = True
              break

          if ignore_item:
            continue

          item_list.append(KeypairItem(region=region.name, account=account, name=kp.name,
                                       config={
                                           'fingerprint': kp.fingerprint
                                       }))
    return item_list, exception_map


class KeypairItem(ChangeItem):
  def __init__(self, region=None, account=None, name=None, config={}):
    super(KeypairItem, self).__init__(
      index=Keypair.index,
      region=region,
      account=account,
      name=name,
      new_config=config)