#     Copyright 2017 Google, Inc.
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
.. module: security_monkey.common.gcp.config
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Tom Melendez <supertom@google.com> @supertom

"""

class ApplicationConfig(object):

    @staticmethod
    def get_version():
        from security_monkey.common.utils import get_version
        return get_version()

class AuditorConfig(object):
    """
    Each Auditor has it's own configuration class defined. They are all guaranteed to contain
    an ISSUE_MAP member, containing issue scores and messages. Auditor-specific configuration
    variables can be defined/modified here as well.
    """
    class GCSBucket():
        MAX_OWNERS_PER_BUCKET = 1

        ISSUE_MAP = {
            'ACL_ALLUSERS_ROLE_READER': {'score': 7, 'msg': "allUsers with Role READER set in bucket ACL."},
            'ACL_ALLUSERS_ROLE_WRITER': {'score': 8, 'msg': "allUsers with Role WRITER set in bucket ACL."},
            'ACL_ALLUSERS_ROLE_OWNER': {'score': 10, 'msg': "allUsers with Role OWNER set in bucket ACL."},
            'ACL_OWNER_MAX': {'score': 7, 'msg': "OWNERS max exceeded in bucket ACL."},
            'ACL_NOT_FOUND': {'score': 10, 'msg': "ACL not found in bucket config."},
            'CORS_PRESENT': {'score': 7, 'msg': "CORS set in bucket config."},
            'CORS_ALL_METHOD': {'score': 10, 'msg': "CORS method '*' allowed in bucket config"},
            'CORS_DELETE_METHOD': {'score': 10, 'msg': "CORS method DELETE allowed in bucket config"},
            'CORS_HEAD_METHOD': {'score': 7, 'msg': "CORS method HEAD allowed in bucket config"},
            'CORS_OPTIONS_METHOD': {'score': 7, 'msg': "CORS method OPTIONS allowed in bucket config"},
            'CORS_POST_METHOD': {'score': 9, 'msg': "CORS method POST allowed in bucket config"},
            'CORS_PUT_METHOD': {'score': 9, 'msg': "CORS method PUT allowed in bucket config"},
            'DEFAULT_OBJECT_ACL_ALLUSERS_ROLE_READER': {'score': 7, 'msg': "allUsers with Role READER set in Default Object ACL."},
            'DEFAULT_OBJECT_ACL_ALLUSERS_ROLE_WRITER': {'score': 8, 'msg': "allUsers with Role WRITER set in Default Object ACL."},
            'DEFAULT_OBJECT_ACL_ALLUSERS_ROLE_OWNER': {'score': 10, 'msg': "allUsers with Role OWNER set in Default Object ACL."},
            'DEFAULT_OBJECT_ACL_OWNER_MAX': {'score': 7, 'msg': "OWNERS max exceeded  in Default Object ACL"},
            'DEFAULT_OBJECT_ACL_NOT_FOUND': {'score': 10, 'msg': "Default Object ACL not found in bucket config."},
        }

    class IAMServiceAccount():
        MAX_SERVICEACCOUNT_KEYS = 4
        ISSUE_MAP = {
            'SA_KEYS_MAX': {
                'score': 7,
                'msg': "Max keys for service account exceeded."},
            'SA_POLICY_ROLE_ACTOR': {
                'score': 6,
                'msg': "ServiceAccount Actor contained in policy."},
        }

    class GCEFirewallRule():
        ISSUE_MAP = {
            'ALLOWED_PORTRANGE_EXISTS': {
                'score': 3,
                'msg': "Port Range Found in Firewall Rule."},
            'SOURCE_RANGES_TRAFFIC_OPEN': {
                'score': 7,
                'msg': "Source range open. Traffic permitted from any host."},
            'TARGET_TAGS_NOT_FOUND': {
                'score': 3,
                'msg': "Target Tags Not Found in Firewall Rule."},
        }

    class GCENetwork():
        ISSUE_MAP = {
            'NET_LEGACY_EXISTS': {
                'score': 8,
                'msg': "Legacy networks are not recommended."},
        }
