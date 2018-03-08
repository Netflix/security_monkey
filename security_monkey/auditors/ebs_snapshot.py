
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
.. module: security_monkey.auditors.ebs_snapshot
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Patrick Kelley <patrick@netflix.com> @monkeysecurity

"""
from security_monkey.auditor import Auditor, Entity
from security_monkey.watchers.ec2.ebs_snapshot import EBSSnapshot


class EBSSnapshotAuditor(Auditor):
    index = EBSSnapshot.index
    i_am_singular = EBSSnapshot.i_am_singular
    i_am_plural = EBSSnapshot.i_am_plural

    def __init__(self, accounts=None, debug=False):
        super(EBSSnapshotAuditor, self).__init__(accounts=accounts, debug=debug)

    # Example permission set:
    # item = {"create_volume_permissions": [
    #     {
    #       "Group": "all"
    #     },
    #     {
    #       "UserId": "123456789012"
    #     },
    #     {
    #       "UserId": "aws-marketplace"
    #     }
    # ]}
    def _get_permissions(self, item, key='UserId'):
        return {perm.get(key) for perm in item.config.get('create_volume_permissions', []) if key in perm}

    def check_friendly_access(self, item):
        for uid in self._get_permissions(item):
            entity = Entity(category='account', value=uid)
            if 'FRIENDLY' in self.inspect_entity(entity, item):
                self.record_friendly_access(item, entity, actions=['createEBSVolume'])

    def check_thirdparty_access(self, item):
        for uid in self._get_permissions(item):
            entity = Entity(category='account', value=uid)
            if 'THIRDPARTY' in self.inspect_entity(entity, item):
                self.record_thirdparty_access(item, entity, actions=['createEBSVolume'])

    def check_unknown_access(self, item):
        for uid in self._get_permissions(item):

            # handled as a special case of internet accessible access.
            if 'aws-marketplace' == uid:
                continue

            entity = Entity(category='account', value=uid)
            if 'UNKNOWN' in self.inspect_entity(entity, item):
                self.record_unknown_access(item, entity, actions=['createEBSVolume'])

    def check_marketplace_access(self, item):
        if 'aws-marketplace' in self._get_permissions(item):
            entity = Entity(category='shared_ebs', value='aws-marketplace')
            self.record_internet_access(item, entity, actions=['createEBSVolume'])

    def check_internet_accessible(self, item):
        if 'all' in self._get_permissions(item, key='Group'):
            entity = Entity(category='shared_ebs', value='public')
            self.record_internet_access(item, entity, actions=['createEBSVolume'])