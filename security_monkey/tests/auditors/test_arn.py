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
.. module: security_monkey.tests.auditors.test_arn
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor::  Mike Grima <mgrima@netflix.com>

"""
from security_monkey.common.arn import ARN
from security_monkey.tests import SecurityMonkeyTestCase
from security_monkey import app, ARN_PREFIX


class ARNTestCase(SecurityMonkeyTestCase):
    def test_from_arn(self):
        proper_arns = [
            'events.amazonaws.com',
            'cloudtrail.amazonaws.com',
            ARN_PREFIX + ':iam::012345678910:root',
            ARN_PREFIX + ':iam::012345678910:role/SomeTestRoleForTesting',
            ARN_PREFIX + ':iam::012345678910:instance-profile/SomeTestInstanceProfileForTesting',
            ARN_PREFIX + ':iam::012345678910:role/*',
            ARN_PREFIX + ':iam::012345678910:role/SomeTestRole*',
            ARN_PREFIX + ':s3:::some-s3-bucket',
            ARN_PREFIX + ':s3:*:*:some-s3-bucket',
            ARN_PREFIX + ':s3:::some-s3-bucket/some/path/within/the/bucket',
            ARN_PREFIX + ':s3:::some-s3-bucket/*',
            ARN_PREFIX + ':ec2:us-west-2:012345678910:instance/*',
            ARN_PREFIX + ':ec2:ap-northeast-1:012345678910:security-group/*',
            ARN_PREFIX + ':ec2:ap-northeast-1:012345678910:security-group/*',
            ARN_PREFIX + ':ec2:gov-west-1:012345678910:instance/*',
            ARN_PREFIX + ':iam::cloudfront:user/CloudFront Origin Access Identity EXXXXXXXXXXXXX'
        ]

        # Proper ARN Tests:
        for arn in proper_arns:
            app.logger.info('Testing Proper ARN: {}'.format(arn))
            arn_obj = ARN(arn)

            self.assertFalse(arn_obj.error)
            if "root" in arn:
                self.assertTrue(arn_obj.root)
            else:
                self.assertFalse(arn_obj.root)

            if ".amazonaws.com" in arn:
                self.assertTrue(arn_obj.service)
            else:
                self.assertFalse(arn_obj.service)

        bad_arns = [
            ARN_PREFIX + ':iam::012345678910',
            ARN_PREFIX + ':iam::012345678910:',
            '*',
            'arn:s3::::',
            "arn:arn:arn:arn:arn:arn"
        ]

        # Improper ARN Tests:
        for arn in bad_arns:
            app.logger.info('Testing IMPROPER ARN: {}'.format(arn))
            arn_obj = ARN(arn)

            self.assertTrue(arn_obj.error)

    def test_from_account_number(self):
        proper_account_numbers = [
            '012345678912',
            '123456789101',
            '123456789101'
        ]

        improper_account_numbers = [
            '*',
            'O12345678912',  # 'O' instead of '0'
            'asdfqwer',
            '123456',
            '89789456314356132168978945',
            '568947897*'
        ]

        # Proper account number tests:
        for accnt in proper_account_numbers:
            app.logger.info('Testing Proper Account Number: {}'.format(accnt))
            arn_obj = ARN(accnt)

            self.assertFalse(arn_obj.error)

        # Improper account number tests:
        for accnt in improper_account_numbers:
            app.logger.info('Testing IMPROPER Account Number: {}'.format(accnt))
            arn_obj = ARN(accnt)

            self.assertTrue(arn_obj.error)

    def test_extract_arns_from_statement_condition(self):
        test_condition_list = [
            'ArnEquals',
            'ForAllValues:ArnEquals',
            'ForAnyValue:ArnEquals',
            'ArnLike',
            'ForAllValues:ArnLike',
            'ForAnyValue:ArnLike',
            'StringLike',
            'ForAllValues:StringLike',
            'ForAnyValue:StringLike',
            'StringEquals',
            'ForAllValues:StringEquals',
            'ForAnyValue:StringEquals'
        ]

        bad_condition_list = [
            'NotACondition',
            'ArnLikeSomethingNotARealCondition'
        ]

        arn_types = [
            ('aws:sourcearn', ARN_PREFIX + ':s3:::some-s3-bucket'),
            ('aws:sourcearn', ARN_PREFIX + ':s3:::some-s3-bucket/*'),
            ('aws:sourcearn', "*"),
            ('aws:sourceowner', '012345678912'),
            ('aws:sourceowner', '*')
        ]

        for condition in test_condition_list:
            for arn_type in arn_types:
                test_condition = {
                    condition: {
                        arn_type[0]: arn_type[1]
                    }
                }

                result = ARN.extract_arns_from_statement_condition(test_condition)
                self.assertIsInstance(result, list)
                self.assertTrue(len(result) > 0)

        for condition in bad_condition_list:
            for arn_type in arn_types:
                test_condition = {
                    condition: {
                        arn_type[0]: arn_type[1]
                    }
                }

                result = ARN.extract_arns_from_statement_condition(test_condition)
                self.assertIsInstance(result, list)
                self.assertTrue(len(result) == 0)
