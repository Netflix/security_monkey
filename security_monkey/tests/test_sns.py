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
from security_monkey.tests import SecurityMonkeyTestCase
from mock import patch
from mock import MagicMock
from security_monkey.auditors.sns import SNSAuditor
from security_monkey.constants import Constants
from security_monkey.exceptions import InvalidARN
#from security_monkey.exceptions import InvalidAWSJSON
from security_monkey.exceptions import InvalidSourceOwner
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.watchers.sns import SNSItem


class SNSTestCase(SecurityMonkeyTestCase):

  @patch('security_monkey.common.sts_connect.connect')
  def test_0_sns_slurp(self, test_patch):
    """Should add an exception to the exception map when
      slurping accounts that don't exist."""
    from security_monkey.watchers.sns import SNS
    import boto.sns

    test_patch.return_value = None
    accounts = ['doesntexist1', 'doesntexist2']
    cw = SNS(accounts=accounts, debug=True)
    #with self.assertRaises(BotoConnectionIssue):
    (items, el) = cw.slurp()
    for account in accounts:
      for region in boto.sns.regions():
        if region.name not in TROUBLE_REGIONS:
          self.assertIn(('sns', account, region.name), el)

  @patch('security_monkey.common.sts_connect.connect')
  def test_1_sns_slurp(self, test_patch):
    """Should add an exception to the exception map when provided with invalid JSON."""

    class MockSNS(object):
      def get_all_topics(self, next_token=None):
        return {'ListTopicsResponse':
                 {'ListTopicsResult':
                   {'NextToken': False,
                    'Topics':
                     [
                       {'TopicArn': 'arn:aws:sns:us-west-2:000000000000:NameZero'
                       },
                       {'TopicArn': 'arn:aws:sns:us-east-1:111111111111:NameOne'
                       }
                     ]
                   }
                 }
               }

      def get_topic_attributes(self, arn):
        return {'GetTopicAttributesResponse':
                 {'GetTopicAttributesResult':
                   {'Attributes':
                     {'Policy': '{"json": "that": "won\'t": "parse"}'
                     }
                   }
                 }
               }

    from security_monkey.watchers.sns import SNS
    import boto.sns
    test_patch.return_value = MockSNS()
    accounts = ['testaccount']
    cw = SNS(accounts=accounts, debug=True)
    (items, el) = cw.slurp()
    for account in accounts:
      for region in boto.sns.regions():
        if region.name not in TROUBLE_REGIONS:
          self.assertIn(('sns', account, region.name, 'arn:aws:sns:us-west-2:000000000000:NameZero'), el)
          self.assertIn(('sns', account, region.name, 'arn:aws:sns:us-east-1:111111111111:NameOne'), el)

  @patch('security_monkey.common.sts_connect.connect')
  def test_2_sns_slurp(self, test_patch):

    class MockSNS(object):
      def get_all_topics(self, next_token=None):
        return {'ListTopicsResponse':
                 {'ListTopicsResult':
                  {'NextToken': False,
                   'Topics':
                     [
                       {'TopicArn': 'arn:aws:sns:us-west-2:000000000000:NameZero'
                       },  # Invalid ARN is missing region:
                       {'TopicArn': 'arn:aws:sns::111111111111:NameOne'
                       }
                     ]
                   }
                 }
               }

      def get_topic_attributes(self, arn):
        return {'GetTopicAttributesResponse':
                 {'GetTopicAttributesResult':
                   {'Attributes':
                     {'Policy': '{"json": "is_fun"}'
                     }
                   }
                 }
               }

    from security_monkey.watchers.sns import SNS
    import boto.sns
    test_patch.return_value = MockSNS()
    accounts = ['testaccount']
    cw = SNS(accounts=accounts, debug=True)
    (items, el) = cw.slurp()
    for account in accounts:
      for region in boto.sns.regions():
        if region.name not in TROUBLE_REGIONS:
          self.assertIn(('sns', account, region.name, 'arn:aws:sns::111111111111:NameOne'), el)

  @patch('security_monkey.common.sts_connect.connect')
  def test_3_sns_slurp(self, test_patch):

    class MockSNS(object):
      def get_all_topics(self):
        return {'ListTopicsResponse':
                 {'ListTopicsResult':
                   {'Topics':
                     [
                       {'TopicArn': 'arn:aws:sns:us-west-2:000000000000:NameZero'
                       }
                     ]
                   }
                 }
               }

      def get_topic_attributes(self, arn):
        return {'GetTopicAttributesResponse':
                 {'GetTopicAttributesResult':
                   {'Attributes':
                     {'Policy': '{"json": "value"}'
                     }
                   }
                 }
               }

    from security_monkey.watchers.sns import SNS
    test_patch.return_value = MockSNS()
    cw = SNS(debug=True)
    (items, el) = cw.slurp()
    for item in items:
      name = item.config['Name']['Name']
      self.assertEqual(name, 'NameZero')
      policy = item.config['SNSPolicy']
      self.assertDictEqual(policy, {"json": "value"})

  def test_empty_snstopicpolicy(self):
    au = SNSAuditor(debug=True)
    obj = SNSItem(region='test-region', account='test-account', name='test-name', config={'SNSPolicy': {}})
    au.check_snstopicpolicy_empty(obj)
    self.assertEquals(len(obj.audit_issues), 1)
    if len(obj.audit_issues) == 1:
      for issue in obj.audit_issues:
        self.assertEquals(issue.score, 1)
        self.assertEquals(issue.issue, "SNS Topic Policy is empty")
        self.assertIsNone(issue.notes)

  def test_crossaccount_snstopicpolicy_method_1(self):
    au = SNSAuditor(debug=True)
    data = {
        'SNSPolicy': {
          'Statement': [
            {
              'Principal': {
                'AWS': '*'
              },
              'Condition': {
                'StringEquals': {
                  'AWS:SourceOwner': '000000000000'
                }
              }
            }
          ]
        }
    }
    obj = SNSItem(region='test-region', account='test-account', name='test-name', config=data)

    au.check_snstopicpolicy_crossaccount(obj)
    self.assertEquals(len(obj.audit_issues), 1)
    if len(obj.audit_issues) == 1:
      for issue in obj.audit_issues:
        self.assertEquals(issue.score, 10)
        self.assertRegexpMatches(issue.issue, "Unknown Cross Account Access from .*")
        self.assertIsNone(issue.notes)

  def test_crossaccount_snstopicpolicy_method_2(self):
    obj = self.check_arn('arn:aws:iam::000000000000:')
    self.assertEquals(len(obj.audit_issues), 1)
    if len(obj.audit_issues) == 1:
      for issue in obj.audit_issues:
        self.assertEquals(issue.score, 10)
        self.assertRegexpMatches(issue.issue, "Unknown Cross Account Access from .*")
        self.assertIsNone(issue.notes)

  def test_crossaccount_snstopicpolicy_method_3(self):
    friend_name = 'friendly'
    Constants.account_by_number = MagicMock(return_value=friend_name)
    obj = self.check_arn('arn:aws:iam::010101010101:')
    self.assertEquals(len(obj.audit_issues), 1)
    if len(obj.audit_issues) == 1:
      for issue in obj.audit_issues:
        self.assertEquals(issue.score, 5)
        expected = "Friendly Cross Account Access from " + friend_name + " to test-account"
        self.assertEqual(expected, issue.issue, "\n" + expected + "\n" + issue.issue)
        self.assertIsNone(issue.notes)

  def test_crossaccount_snstopicpolicy_method_4(self):
    # Bad ARN
    with self.assertRaises(InvalidARN):
      self.check_arn('arn::aws:iam:-:010101010101:')

  def test_crossaccount_snstopicpolicy_method_5(self):
    au = SNSAuditor(debug=True)
    data = {
        'SNSPolicy': {
          'Statement': [
            {
              'Principal': {
                'AWS': '*'
              },
              'Condition': {
                'StringEquals': {
                  # Missing SourceOwner
                }
              }
            }
          ]
        }
    }
    obj = SNSItem(region='test-region', account='test-account', name='test-name', config=data)
    au.check_snstopicpolicy_crossaccount(obj)
    self.assertEquals(len(obj.audit_issues), 1)
    issue = obj.audit_issues[0]
    self.assertEqual(issue.score, 10)
    self.assertEqual(issue.issue, "SNS Topic open to everyone")

  def test_crossaccount_snstopicpolicy_method_6(self):
    au = SNSAuditor(debug=True)
    data = {
        'SNSPolicy': {
          'Statement': [
            {
              'Principal': {
                'AWS': '*'
              },
              'Condition': {
                'StringEquals': {
                  'AWS:SourceOwner': 'BADDEADBEEF'
                }
              }
            }
          ]
        }
    }
    obj = SNSItem(region='test-region', account='test-account', name='test-name', config=data)
    with self.assertRaises(InvalidSourceOwner):
      au.check_snstopicpolicy_crossaccount(obj)

  def check_arn(self, arn):
    au = SNSAuditor(debug=True)
    data = {
        'SNSPolicy': {
          'Statement': [
            {
              'Principal': {
                'AWS': arn
              }
            }
          ]
        }
    }
    obj = SNSItem(region='test-region', account='test-account', name='test-name', config=data)

    au.check_snstopicpolicy_crossaccount(obj)
    return obj
