#!/usr/bin/env python

# Copyright 2014 Rocket-Internet
# Luca Bruno <luca.bruno@rocket-internet.de>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SecurityMonkey AWS role provisioning script
Grab credentials from ~/.boto (or other standard credentials sources).
Optionally accept "profile_name" as CLI parameter.
"""

import sys, json
import urllib
import boto

# FILL THIS IN
# Supervision account that can assume monitoring role
secmonkey_arn = 'arn:aws:iam::<awsaccountnumber>:role/SecurityMonkeyInstanceProfile'

trust_relationship = \
'''
{
  "Version": "2008-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "AWS": "%s"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
'''

# Role with restricted security policy (list/get only)
role_name = 'SecurityMonkey'
role_policy_name = 'SecurityMonkeyPolicy'

policy = \
'''
{
  "Statement": [
    {
      "Action": [
        "cloudwatch:Describe*",
        "cloudwatch:Get*",
        "cloudwatch:List*",
        "ec2:Describe*",
        "elasticloadbalancing:Describe*",
        "iam:List*",
        "iam:Get*",
        "route53:Get*",
        "route53:List*",
        "rds:Describe*",
        "s3:GetBucketAcl",
        "s3:GetBucketCORS",
        "s3:GetBucketLocation",
        "s3:GetBucketLogging",
        "s3:GetBucketPolicy",
        "s3:GetBucketVersioning",
        "s3:GetLifecycleConfiguration",
        "s3:ListAllMyBuckets",
        "sdb:GetAttributes",
        "sdb:List*",
        "sdb:Select*",
        "ses:Get*",
        "ses:List*",
        "sns:Get*",
        "sns:List*",
        "sqs:GetQueueAttributes",
        "sqs:ListQueues",
        "sqs:ReceiveMessage"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
'''

def main(profile = None):
  # Sanitize JSON
  assume_policy = json.dumps(json.loads(trust_relationship % secmonkey_arn))
  security_policy = json.dumps(json.loads(policy))

  # Connect to IAM
  (role_exist, current_policy) = (False, "")
  try:
    iam = boto.connect_iam(profile_name = profile)
  except boto.exception.NoAuthHandlerFound:
    sys.exit("Authentication failed, please check your credentials under ~/.boto")

  # Check if role already exists
  rlist = iam.list_roles()
  for r in rlist['list_roles_response']['list_roles_result']['roles']:
    if r['role_name'] == role_name:
      role_exist = True
      current_policy = json.loads(urllib.unquote(r['assume_role_policy_document']))
      for p in current_policy['Statement']:
        if p['Action'] == 'sts:AssumeRole':
          if secmonkey_arn in p['Principal']['AWS'] :
            # Already ok
            sys.exit('Role "%s" already configured, not touching it.' % role_name)
          else:
            # Add another monitoring account
            new_policy = [secmonkey_arn]
            new_policy.extend(p['Principal']['AWS'])
            p['Principal']['AWS'] = new_policy
      assume_policy = json.dumps(current_policy)

  # Add SecurityMonkey monitoring role and link it to supervisor ARN
  if not role_exist:
    role = iam.create_role(role_name, assume_policy)
  else:
    role = iam.update_assume_role_policy(role_name, assume_policy)

  # Add our own role policy
  iam.put_role_policy(role_name, role_policy_name, security_policy)
  print('Added role "%s", linked to ARN "%s".' % (role_name, secmonkey_arn))

if __name__ == "__main__":
  profile = None
  if len(sys.argv) >= 2:
    profile = sys.argv[1]
  main(profile)
