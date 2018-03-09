#     Copyright 2017 Netflix, Inc.
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
.. module: security_monkey.common.s3_canonical
    :platform: Unix
    :synopsis: Fetchs the S3 canonical IDs for a given AWS account.

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
from cloudaux.decorators import iter_account_region
from cloudaux.aws.s3 import list_buckets

from security_monkey import app, db
from security_monkey.datastore import AccountTypeCustomValues
from security_monkey.decorators import record_exception
from security_monkey import AWS_DEFAULT_REGION

def get_canonical_ids(accounts, override=False):
    """
    Given a list of AWS Account IDs, reach out to AWS to fetch the Canonical IDs
    :param override:
    :param accounts:
    :return:
    """
    if not override:
        app.logger.info("[@] Override flag was not passed in -- will skip over accounts with a canonical "
                        "ID associated.")

    # Loop over each account manually:
    for account in accounts:
        # Does the account already have the canonical ID set?
        current_canonical = AccountTypeCustomValues.query \
            .filter(AccountTypeCustomValues.name == "canonical_id",
                    AccountTypeCustomValues.account_id == account.id).first()
        if not override and current_canonical:
            app.logger.info("[/] Account {} already has a canonical ID associated... Skipping...".format(account.name))
            continue

        @iter_account_region("s3", accounts=[account.identifier], regions=[AWS_DEFAULT_REGION],
                             assume_role=account.getCustom("role_name") or "SecurityMonkey",
                             session_name="SecurityMonkey", conn_type="dict")
        def loop_over_accounts(**kwargs):
            app.logger.info("[-->] Fetching canonical ID for account: {}".format(account.name))

            return fetch_id(index="s3", exception_record_region=AWS_DEFAULT_REGION, account_name=account.name,
                            exception_map={}, **kwargs)

        result = loop_over_accounts()

        if not result:
            app.logger.error("[x] Did not receive a proper response back. Check the exception log for details.")
            continue

        # Fetch out the owner:
        app.logger.info("[+] Associating Canonical ID: {} with account: {}".format(result[0]["Owner"]["ID"],
                                                                                   account.name))

        if not current_canonical:
            current_canonical = AccountTypeCustomValues(account_id=account.id, name="canonical_id")

        current_canonical.value = result[0]["Owner"]["ID"]

        db.session.add(current_canonical)
        db.session.commit()


@record_exception(source="canonical-id-fetcher", pop_exception_fields=True)
def fetch_id(**kwargs):
    return list_buckets(**kwargs["conn_dict"])
