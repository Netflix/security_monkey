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
        return repr("Problem Connecting to {}/{}/{}".format(
            self.tech, self.account, self.region))


class S3PermissionsIssue(SecurityMonkeyException):
    """Boto could not read metadata about an S3 bucket. Check permissions."""

    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        app.logger.info(self)

    def __str__(self):
        return repr("AWS returned an exception while attempting " +
                    "to obtain information on a bucket I should " +
                    "have access to. Bucket Name: {}".format(self.bucket_name))


class S3ACLReturnedNoneDisplayName(SecurityMonkeyException):
    """The XML representation of an S3 ACL is not providing a proper DisplayName."""

    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        app.logger.info(self)

    def __str__(self):
        return repr("AWS returned <DisplayName>None</DisplayName>" +
                    " in the output of bhandle.get_acl().to_xml()." +
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


class AccountNameExists(SecurityMonkeyException):
    """Security Monkey Account name exists... cannot rename or create an account with that name"""

    def __init__(self, account_name):
        self.account_name = account_name
        app.logger.info(self)

    def __str__(self):
        return repr("Account with name: {} already exists. Cannnot create"
                    " or rename account with this name.".format(self.account_name))


class ZoneIDNotFound(SecurityMonkeyException):
    """Zone ID is not found during lookup"""

    def __init__(self, domain):
        self.domain = domain
        app.logger.error(self)

    def __str__(self):
        return repr("Given domain ({}) not found in hosted zones".format(self.domain))


class GitHubCredsError(SecurityMonkeyException):
    """Unable to fetch GitHub credentials file"""

    def __init__(self, account):
        self.account = account
        app.logger.info(self)

    def __str__(self):
        return repr("Unable to load GitHub credentials for account: {}".format(self.account))


class InvalidResponseCodeFromGitHubError(SecurityMonkeyException):
    """Unable to fetch data from GitHub"""

    def __init__(self, organization, response_code):
        self.organization = organization
        self.response_code = response_code
        app.logger.info(self)

    def __str__(self):
        return repr("Unable to load data from GitHub for the org: {} -- received HTTP response: {}".format(
            self.organization, self.response_code
        ))


class InvalidResponseCodeFromGitHubRepoError(SecurityMonkeyException):
    """Unable to fetch data from GitHub for a given repo"""

    def __init__(self, organization, repo, response_code):
        self.organization = organization
        self.repo = repo
        self.response_code = response_code
        app.logger.info(self)

    def __str__(self):
        return repr("Unable to load data from GitHub for the repo: {}/{} -- received HTTP response: {}".format(
            self.organization, self.repo, self.response_code
        ))


class UnableToIssueGoogleAuthToken(SecurityMonkeyException):
    """Google oauth token was not issued"""

    def __init__(self, error_message):
        self.error_message = error_message
        app.logger.error(self)


class UnableToAccessGoogleEmail(SecurityMonkeyException):
    """Google oauth token was issued but Google+ API can't be accessed to fetch user details"""

    def __init__(self):
        self.error_message = "Unable to fetch user e-mail. Please ensure your application has Google+ API access"
        app.logger.error(self)


class InvalidCeleryConfigurationType(SecurityMonkeyException):
    """Invalid Security Monkey Celery configuration type"""

    def __init__(self, variable, required_type, value_type):
        self.error_message = "Incorrect type for Security Monkey celery configuration variable: '{}', required: {}, " \
                             "actual: {}".format(variable, required_type.__name__, value_type.__name__)
