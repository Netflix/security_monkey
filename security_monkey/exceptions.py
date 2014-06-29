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
.. module: exceptions
    :synopsis: Defines all security_monkey specific exceptions

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

from security_monkey import app


class SecurityMonkeyException(Exception):
    """Base class for all security monkey exceptions."""
    pass


class InvalidARN(SecurityMonkeyException):
    """Found an indecipherable ARN"""
    def __init__(self, bad_arn):
        self.bad_arn = bad_arn
        app.logger.info(self)

    def __str__(self):
        return repr("Given an invalid ARN: {}".format(self.bad_arn))


class InvalidSourceOwner(SecurityMonkeyException):
    """Source Owners should be an integer representing an AWS account owner."""
    def __init__(self, bad_source_owner):
        self.bad_source_owner = bad_source_owner
        app.logger.info(self)

    def __str__(self):
        return repr("Given an invalid SourceOwner: {}".format(self.bad_source_owner))


class InvalidAWSJSON(SecurityMonkeyException):
    """The JSON returned from AWS is not valid."""
    def __init__(self, bad_json):
        self.bad_json = bad_json
        app.logger.info(self)

    def __str__(self):
        return repr("Could not parse invalid JSON from AWS:\n {}".format(self.bad_json))


class BotoConnectionIssue(SecurityMonkeyException):
    """Boto could not connect.  This could be a permissions issue."""
    def __init__(self, connection_message, tech, account, region):
        self.connection_message = connection_message
        self.tech = tech
        self.account = account
        self.region = region
        app.logger.info(self)

    def __str__(self):
        return repr("Problem Connecting to {}/{}/{}:\n{}".format(
            self.tech, self.account, self.region, self.connection_message))


class S3PermissionsIssue(SecurityMonkeyException):
    """Boto could not read metadata about an S3 bucket. Check permissions."""
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        app.logger.info(self)

    def __str__(self):
        return repr("AWS returned an exception while attempting "+
                    "to obtain information on a bucket I should "+
                    "have access to. Bucket Name: {}".format(self.bucket_name))

class S3ACLReturnedNoneDisplayName(SecurityMonkeyException):
    """The XML representation of an S3 ACL is not providing a proper DisplayName."""
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        app.logger.info(self)

    def __str__(self):
        return repr("AWS returned <DisplayName>None</DisplayName>"+
                    " in the output of bhandle.get_acl().to_xml()."+
                    " Bucket Name:{}".format(self.bucket_name))

class AWSRateLimitReached(SecurityMonkeyException):
    """Security Monkey is being throttled by AWS."""
    def __init__(self, connection_message, tech, account, region):
        self.connection_message = connection_message
        self.tech = tech
        self.account = account
        self.region = region
        app.logger.info(self)

    def __str__(self):
        return repr("Likely reached the AWS rate limit. {}/{}/{}:\n{}".format(
            self.tech, self.account, self.region, self.connection_message))
