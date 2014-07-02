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
.. module: security_monkey.constants
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

# Ignore security groups whose names begin with "cass_"
# There are a number of cassandra auto-generated security groups
# that are constantly changing.
# IAM SSL does not implement the ignore logic.
IGNORE_PREFIX = {
  'sqs': [],
  'elb': [],
  'rds': [],
  'securitygroup': [],
  's3': [],
  'iamuser': [],
  'iamgroup': [],
  'iamrole': [],
  'keypair': [],
  'sns': [],
}

# SM will not alert on exceptions that occur while attempting to retrieve data
# from these regions.  In our case, we do not have permissions to these regions.
TROUBLE_REGIONS = ['cn-north-1', 'us-gov-west-1']

