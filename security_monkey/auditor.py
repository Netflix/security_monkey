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
.. module: security_monkey.auditor
    :platform: Unix
    :synopsis: This class is subclassed to add audit rules.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com>

"""
from six import string_types, text_type

from security_monkey import app, datastore, db
from security_monkey.watcher import ChangeItem, ensure_item_has_latest_revision_id
from security_monkey.common.jinja import get_jinja_env
from security_monkey.datastore import User, AuditorSettings, Item, ItemAudit, Technology, Account, ItemAuditScore, AccountPatternAuditScore
from security_monkey.common.utils import send_email
from security_monkey.account_manager import get_account_by_name
from security_monkey.alerters.custom_alerter import report_auditor_changes
from security_monkey.datastore import Account, Item, Technology, NetworkWhitelistEntry
from policyuniverse.arn import ARN
from sqlalchemy import and_
from collections import defaultdict
from threading import Lock
import json
import netaddr
import ipaddr
import re
import pkg_resources


auditor_registry = defaultdict(list)


class Categories:
    """ Define common issue categories to maintain consistency. """
    # Resource Policies:
    INTERNET_ACCESSIBLE = 'Internet Accessible'
    INTERNET_ACCESSIBLE_NOTES = '{entity} Actions: {actions}'
    INTERNET_ACCESSIBLE_NOTES_SG = '{entity} Access: [{access}]'

    FRIENDLY_CROSS_ACCOUNT = 'Friendly Cross Account'
    FRIENDLY_CROSS_ACCOUNT_NOTES = '{entity} Actions: {actions}'
    FRIENDLY_CROSS_ACCOUNT_NOTES_SG = '{entity} Access: [{access}]'

    THIRDPARTY_CROSS_ACCOUNT = 'Thirdparty Cross Account'
    THIRDPARTY_CROSS_ACCOUNT_NOTES = '{entity} Actions: {actions}'
    THIRDPARTY_CROSS_ACCOUNT_NOTES_SG = '{entity} Access: [{access}]'

    UNKNOWN_ACCESS = 'Unknown Access'
    UNKNOWN_ACCESS_NOTES = '{entity} Actions: {actions}'
    UNKNOWN_ACCESS_NOTES_SG = '{entity} Access: [{access}]'

    PARSE_ERROR = 'Parse Error'
    PARSE_ERROR_NOTES = 'Could not parse {input_type} - {input}'

    CROSS_ACCOUNT_ROOT = 'Cross-Account Root IAM'
    CROSS_ACCOUNT_ROOT_NOTES = '{entity} Actions: {actions}'

    # IAM Policies:
    ADMIN_ACCESS = 'Administrator Access'
    ADMIN_ACCESS_NOTES = 'Actions: {actions} Resources: {resource}'

    SENSITIVE_PERMISSIONS = 'Sensitive Permissions'
    SENSITIVE_PERMISSIONS_NOTES_1 = 'Actions: {actions} Resources: {resource}'
    SENSITIVE_PERMISSIONS_NOTES_2 = 'Service [{service}] Category: [{category}] Resources: {resource}'

    STATEMENT_CONSTRUCTION = 'Awkward Statement Construction'
    STATEMENT_CONSTRUCTION_NOTES = 'Construct: {construct}'

    # Anywhere
    INFORMATIONAL = 'Informational'
    INFORMATIONAL_NOTES = '{description}{specific}'

    ROTATION = 'Needs Rotation'
    ROTATION_NOTES = '{what} last rotated {requirement} on {date}'

    UNUSED = 'Unused Access'
    UNUSED_NOTES = '{what} last used {requirement} on {date}'

    INSECURE_CONFIGURATION = 'Insecure Configuration'
    INSECURE_CONFIGURATION_NOTES = '{description}'

    RECOMMENDATION = 'Recommendation'
    RECOMMENDATION_NOTES = '{description}'

    INSECURE_TLS = 'Insecure TLS'
    INSECURE_TLS_NOTES = 'Policy: [{policy}] Port: {port} Reason: [{reason}]'
    INSECURE_TLS_NOTES_2 = 'Policy: [{policy}] Port: {port} Reason: [{reason}] CVE: [{cve}]'

    # TODO
    # 	INSECURE_CERTIFICATE = 'Insecure Certificate'


class Entity:
    """ Entity instances provide a place to map policy elements like s3:my_bucket to the related account. """
    def __init__(self, category, value, account_name=None, account_identifier=None):
        self.category = category
        self.value = value
        self.account_name = account_name
        self.account_identifier = account_identifier

    @staticmethod
    def from_tuple(entity_tuple):
        return Entity(category=entity_tuple.category, value=entity_tuple.value)

    def __str__(self):
        strval = ''
        if self.account_name or self.account_identifier:
            strval = 'Account: [{identifier}/{account_name}] '.format(identifier=self.account_identifier, account_name=self.account_name)
        strval += 'Entity: [{category}:{value}]'.format(category=self.category, value=self.value)
        return strval

    def __repr__(self):
        return self.__str__()

class AuditorType(type):
    def __init__(cls, name, bases, attrs):
        super(AuditorType, cls).__init__(name, bases, attrs)
        if cls.__name__ != 'Auditor' and cls.index:
            # Only want to register auditors explicitly loaded by find_modules or entry points
            plugin_names = [x.name for x in pkg_resources.iter_entry_points('security_monkey.plugins')]
            if not '.' in cls.__module__ or cls.__module__ in plugin_names: 
                found = False
                for auditor in auditor_registry[cls.index]:
                    if auditor.__module__ == cls.__module__ and auditor.__name__ == cls.__name__:
                        found = True
                        break
                if not found:
                    app.logger.debug("Registering auditor {} {}.{}".format(cls.index, cls.__module__, cls.__name__))
                    auditor_registry[cls.index].append(cls)


def add(to, key, value):
    if not key:
        return
    if key in to:
        to[key].add(value)
    else:
        to[key] = set([value])


class Auditor(object, metaclass=AuditorType):
    """
    This class (and subclasses really) run a number of rules against the configurations
    and look for any violations.  These violations are saved with the object and a report
    is made available via the Web UI and through email.
    """
    index = None          # Should be overridden
    i_am_singular = None  # Should be overridden
    i_am_plural = None    # Should be overridden
    support_auditor_indexes = []
    support_watcher_indexes = []
    OBJECT_STORE = defaultdict(dict)
    OBJECT_STORE_LOCK = Lock()

    def __init__(self, accounts=None, debug=False):
        self.datastore = datastore.Datastore()
        self.accounts = accounts
        self.debug = debug
        self.items = []
        self.team_emails = app.config.get('SECURITY_TEAM_EMAIL', [])
        self.emails = []
        self.current_support_items = {}
        self.override_scores = None
        self.current_method_name = None

        if isinstance(self.team_emails,  string_types):
            self.emails.append(self.team_emails)
        elif isinstance(self.team_emails, (list, tuple)):
            self.emails.extend(self.team_emails)
        else:
            app.logger.info("Auditor: SECURITY_TEAM_EMAIL contains an invalid type")

        for account in self.accounts:
            users = User.query.filter(User.daily_audit_email==True).filter(User.accounts.any(name=account)).all()
            self.emails.extend([user.email for user in users])

    def load_policies(self, item, policy_keys):
        """For a given item, return a list of all resource policies.

        Most items only have a single resource policy, typically found
        inside the config with the key, "Policy".

        Some technologies have multiple resource policies.  A lambda function
        is an example of an item with multiple resource policies.

        The lambda function auditor can define a list of `policy_keys`.  Each
        item in this list is the dpath to one of the resource policies.

        The `policy_keys` defaults to ['Policy'] unless overriden by a subclass.

        Returns:
            list of Policy objects
        """
        import dpath.util
        from dpath.exceptions import PathNotFound
        from policyuniverse.policy import Policy

        policies = list()
        for key in policy_keys:
            try:
                policy = dpath.util.values(item.config, key, separator='$')
                if isinstance(policy, list):
                    for p in policy:
                        if not p:
                            continue
                        if isinstance(p, list):
                            policies.extend([Policy(pp) for pp in p])
                        else:
                            policies.append(Policy(p))
                else:
                    policies.append(Policy(policy))
            except PathNotFound:
                continue
        return policies

    def _issue_matches_listeners(self, item, issue):
        """
        Verify issue is on a port for which the ALB/ELB/RDS contains a listener.
        Entity: [cidr:::/0] Access: [ingress:tcp:80]
        """
        if not issue.notes:
            return False

        protocol_and_ports = self._get_listener_ports_and_protocols(item)
        issue_regex = r'Entity: \[[^\]]+\] Access: \[(.+)\:(.+)\:(.+)\]'
        match = re.search(issue_regex, issue.notes)
        if not match:
            return False

        direction = match.group(1)
        protocol = match.group(2)
        port = match.group(3)

        listener_ports = protocol_and_ports.get(protocol.upper(), [])

        if direction != 'ingress':
            return False

        if protocol == 'all_protocols':
            return True

        if protocol == 'icmp':
            # Although VPC ELBs may allow ICMP to pass through, I don't really
            # consider that to be Internet Accessible.
            # Would also produce funky results for RDS, ES, etc.
            return False

        match = re.search(r'(-?\d+)-(-?\d+)', port)
        if match:
            from_port = int(match.group(1))
            to_port = int(match.group(2))
        else:
            from_port = to_port = int(port)

        for listener_port in listener_ports:
            if int(listener_port) >= from_port and int(listener_port) <= to_port:
                return True
        return False

    @classmethod
    def _load_object_store(cls):
        with cls.OBJECT_STORE_LOCK:
            if not cls.OBJECT_STORE:
                cls._load_s3_buckets()
                cls._load_userids()
                cls._load_accounts()
                cls._load_elasticips()
                cls._load_vpcs()
                cls._load_vpces()
                cls._load_natgateways()
                cls._load_network_whitelist()
                cls._merge_cidrs()


    @classmethod
    def _merge_cidrs(cls):
        """
        We learned about CIDRs from the following functions:
        -   _load_elasticips()
        -   _load_vpcs()
        -   _load_vpces()
        -   _load_natgateways()
        -   _load_network_whitelist()

        These cidr's are stored in the OBJECT_STORE in a way that is not optimal:

            OBJECT_STORE['cidr']['54.0.0.1'] = set(['123456789012'])
            OBJECT_STORE['cidr']['54.0.0.0'] = set(['123456789012'])
            ...
            OBJECT_STORE['cidr']['54.0.0.255/32'] = set(['123456789012'])

        The above example is attempting to illustrate that account `123456789012`
        contains `54.0.0.0/24`, maybe from 256 elastic IPs.

        If a resource policy were attempting to ingress this range as a `/24` instead
        of as individual IPs, it would not work.  We need to use the `cidr_merge`
        method from the `netaddr` library.  We need to preserve the account identifiers
        that are associated with each cidr as well.

        # Using:
        # https://netaddr.readthedocs.io/en/latest/tutorial_01.html?highlight=summarize#summarizing-list-of-addresses-and-subnets
        # import netaddr
        # netaddr.cidr_merge(ip_list)

        Step 1: Group CIDRs by account:
        #   ['123456789012'] = ['IP', 'IP']

        Step 2:
        Merge each account's cidr's separately and repalce the OBJECT_STORE['cidr'] entry.

        Return:
            `None`.  Mutates the cls.OBJECT_STORE['cidr'] datastructure.
        """
        if not 'cidr' in cls.OBJECT_STORE:
            return

        # step 1
        merged = defaultdict(set)
        for cidr, accounts in list(cls.OBJECT_STORE['cidr'].items()):
            for account in accounts:
                merged[account].add(cidr)

        del cls.OBJECT_STORE['cidr']

        # step 2
        for account, cidrs in list(merged.items()):
            merged_cidrs = netaddr.cidr_merge(cidrs)
            for cidr in merged_cidrs:
                add(cls.OBJECT_STORE['cidr'], str(cidr), account)

    @classmethod
    def _load_s3_buckets(cls):
        """Store the S3 bucket ARNs from all our accounts"""
        results = cls._load_related_items('s3')
        for item in results:
            add(cls.OBJECT_STORE['s3'], item.name, item.account.identifier)

    @classmethod
    def _load_vpcs(cls):
        """Store the VPC IDs. Also, extract & store network/NAT ranges."""
        results = cls._load_related_items('vpc')
        for item in results:
            add(cls.OBJECT_STORE['vpc'], item.latest_config.get('id'), item.account.identifier)
            add(cls.OBJECT_STORE['cidr'], item.latest_config.get('cidr_block'), item.account.identifier)

            vpcnat_tags = text_type(item.latest_config.get('tags', {}).get('vpcnat', ''))
            vpcnat_tag_cidrs = vpcnat_tags.split(',')
            for vpcnat_tag_cidr in vpcnat_tag_cidrs:
                add(cls.OBJECT_STORE['cidr'], vpcnat_tag_cidr.strip(), item.account.identifier)

    @classmethod
    def _load_vpces(cls):
        """Store the VPC Endpoint IDs."""
        results = cls._load_related_items('endpoint')
        for item in results:
            add(cls.OBJECT_STORE['vpce'], item.latest_config.get('id'), item.account.identifier)

    @classmethod
    def _load_elasticips(cls):
        """Store the Elastic IPs."""
        results = cls._load_related_items('elasticip')
        for item in results:
            add(cls.OBJECT_STORE['cidr'], item.latest_config.get('public_ip'), item.account.identifier)
            add(cls.OBJECT_STORE['cidr'], item.latest_config.get('private_ip_address'), item.account.identifier)

    @classmethod
    def _load_natgateways(cls):
        """Store the NAT Gateway CIDRs."""
        results = cls._load_related_items('natgateway')
        for gateway in results:
            for address in gateway.latest_config.get('nat_gateway_addresses', []):
                add(cls.OBJECT_STORE['cidr'], address['public_ip'], gateway.account.identifier)
                add(cls.OBJECT_STORE['cidr'], address['private_ip'], gateway.account.identifier)

    @classmethod
    def _load_network_whitelist(cls):
        """Stores the Network Whitelist CIDRs."""
        whitelist_entries = NetworkWhitelistEntry.query.all()
        for entry in whitelist_entries:
            add(cls.OBJECT_STORE['cidr'], entry.cidr, '000000000000')

    @classmethod
    def _load_userids(cls):
        """Store the UserIDs from all IAMUsers and IAMRoles."""
        user_results = cls._load_related_items('iamuser')
        role_results = cls._load_related_items('iamrole')

        for item in user_results:
            fixed_item = ensure_item_has_latest_revision_id(item)
            if not fixed_item:
                continue

            add(cls.OBJECT_STORE['userid'], fixed_item.latest_config.get('UserId'), fixed_item.account.identifier)

        for item in role_results:
            fixed_item = ensure_item_has_latest_revision_id(item)
            if not fixed_item:
                continue

            add(cls.OBJECT_STORE['userid'], fixed_item.latest_config.get('RoleId'), fixed_item.account.identifier)

    @classmethod
    def _load_accounts(cls):
        """Store the account IDs of all friendly/thirdparty accounts."""
        friendly_accounts = Account.query.filter(Account.third_party == False).all()
        third_party = Account.query.filter(Account.third_party == True).all()

        cls.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'] = list()
        cls.OBJECT_STORE['ACCOUNTS']['FRIENDLY'] = set()
        cls.OBJECT_STORE['ACCOUNTS']['THIRDPARTY'] = set()

        for account in friendly_accounts:
            add(cls.OBJECT_STORE['ACCOUNTS'], 'FRIENDLY', account.identifier)
            cls.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'].append(dict(
                name=account.name,
                identifier=account.identifier,
                label='friendly',
                s3_name=account.getCustom('s3_name'),
                s3_canonical_id=account.getCustom('canonical_id')))

        for account in third_party:
            add(cls.OBJECT_STORE['ACCOUNTS'], 'THIRDPARTY', account.identifier)
            cls.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS'].append(dict(
                name=account.name,
                identifier=account.identifier,
                label='thirdparty',
                s3_name=account.getCustom('s3_name'),
                s3_canonical_id=account.getCustom('canonical_id')))

    @staticmethod
    def _load_related_items(technology_name):
        query = Item.query.join((Technology, Technology.id == Item.tech_id))
        query = query.filter(Technology.name==technology_name)
        return query.all()

    def _get_account(self, key, value):
        """ _get_account('s3_name', 'blah') """
        if key == 'aws':
            return dict(name='AWS', identifier='AWS')
        for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS']:
            if text_type(account.get(key, '')).lower() == value.lower():
                return account

    def inspect_entity(self, entity, item):
        """A entity can represent an:

        - ARN
        - Account Number
        - UserID
        - CIDR
        - VPC
        - VPCE

        Determine if the who is in our current account. Add the associated account
        to the entity.

        Return:
            'SAME' - The who is in our same account.
            'FRIENDLY' - The who is in an account Security Monkey knows about.
            'UNKNOWN' - The who is in an account Security Monkey does not know about.
        """
        same = Account.query.filter(Account.name == item.account).first()

        if entity.category in ['arn', 'principal']:
            return self.inspect_entity_arn(entity, same, item)
        if entity.category == 'account':
            return set([self.inspect_entity_account(entity, entity.value, same)])
        if entity.category == 'security_group':
            account_identifier = entity.value.split('/')[0]
            entity.value = entity.value.split('/')[1]
            result_set = set([self.inspect_entity_account(entity, account_identifier, same)])
            return result_set
        if entity.category == 'userid':
            return self.inspect_entity_userid(entity, same)
        if entity.category == 'cidr':
            return self.inspect_entity_cidr(entity, same)
        if entity.category == 'vpc':
            return self.inspect_entity_vpc(entity, same)
        if entity.category == 'vpce':
            return self.inspect_entity_vpce(entity, same)

        return 'ERROR'

    def inspect_entity_arn(self, entity, same, item):
        arn_input = entity.value
        if arn_input == '*':
            return set(['UNKNOWN'])

        arn = ARN(arn_input)
        if arn.error:
            self.record_arn_parse_issue(item, arn_input)

        if arn.tech == 's3':
            return self.inspect_entity_s3(entity, arn.name, same)

        return set([self.inspect_entity_account(entity, arn.account_number, same)])

    def inspect_entity_account(self, entity, account_number, same):

        # Enrich the entity with account data if available.
        for account in self.OBJECT_STORE['ACCOUNTS']['DESCRIPTIONS']:
            if account['identifier'] == account_number:
                entity.account_name = account['name']
                entity.account_identifier = account['identifier']
                break

        if account_number == '000000000000':
            return 'SAME'
        if account_number == same.identifier:
            return 'SAME'
        if account_number in self.OBJECT_STORE['ACCOUNTS']['FRIENDLY']:
            return 'FRIENDLY'
        if account_number in self.OBJECT_STORE['ACCOUNTS']['THIRDPARTY']:
            return 'THIRDPARTY'
        return 'UNKNOWN'

    def inspect_entity_s3(self, entity, bucket_name, same):
        return self.inspect_entity_generic('s3', entity, bucket_name, same)

    def inspect_entity_userid(self, entity, same):
        return self.inspect_entity_generic('userid', entity, entity.value.split(':')[0], same)

    def inspect_entity_vpc(self, entity, same):
        return self.inspect_entity_generic('vpc', entity, entity.value, same)

    def inspect_entity_vpce(self, entity, same):
        return self.inspect_entity_generic('vpce', entity, entity.value, same)

    def inspect_entity_cidr(self, entity, same):
        values = set()
        for str_cidr in self.OBJECT_STORE.get('cidr', []):
            if ipaddr.IPNetwork(entity.value) in ipaddr.IPNetwork(str_cidr):
                for account in self.OBJECT_STORE['cidr'].get(str_cidr, []):
                    values.add(self.inspect_entity_account(entity, account, same))
        if not values:
            return set(['UNKNOWN'])
        return values

    def inspect_entity_generic(self, key, entity, item, same):
        if item in self.OBJECT_STORE.get(key, []):
            values = set()
            for account in self.OBJECT_STORE[key].get(item, []):
                values.add(self.inspect_entity_account(entity, account, same))
            return values
        return set(['UNKNOWN'])

    def record_internet_access(self, item, entity, actions, score=10, source='resource_policy'):
        tag = Categories.INTERNET_ACCESSIBLE
        if source == 'security_group':
            notes = Categories.INTERNET_ACCESSIBLE_NOTES_SG
            notes = notes.format(entity=entity, access=actions)
        else:
            notes = Categories.INTERNET_ACCESSIBLE_NOTES
            notes = notes.format(entity=entity, actions=json.dumps(actions))

        action_instructions = None
        if source == 'resource_policy':
            action_instructions = "An {singular} ".format(singular=self.i_am_singular)
            action_instructions += "with { 'Principal': { 'AWS': '*' } } must also have a strong condition block or it is Internet Accessible. "
        self.add_issue(score, tag, item, notes=notes, action_instructions=action_instructions)

    def record_friendly_access(self, item, entity, actions, score=0, source=None):
        tag = Categories.FRIENDLY_CROSS_ACCOUNT
        if source == 'security_group':
            notes = Categories.FRIENDLY_CROSS_ACCOUNT_NOTES_SG
            notes = notes.format(entity=entity, access=actions)
        else:
            notes = Categories.FRIENDLY_CROSS_ACCOUNT_NOTES
            notes = notes.format(entity=entity, actions=json.dumps(actions))

        self.add_issue(0, tag, item, notes=notes)

    def record_thirdparty_access(self, item, entity, actions, score=0, source=None):
        tag = Categories.THIRDPARTY_CROSS_ACCOUNT
        if source == 'security_group':
            notes = Categories.THIRDPARTY_CROSS_ACCOUNT_NOTES_SG
            notes = notes.format(entity=entity, access=actions)
        else:
            notes = Categories.THIRDPARTY_CROSS_ACCOUNT_NOTES
            notes = notes.format(entity=entity, actions=json.dumps(actions))

        self.add_issue(0, tag, item, notes=notes)

    def record_unknown_access(self, item, entity, actions, score=0, source=None):
        tag = Categories.UNKNOWN_ACCESS
        if source == 'security_group':
            notes = Categories.UNKNOWN_ACCESS_NOTES_SG
            notes = notes.format(entity=entity, access=actions)
        else:
            notes = Categories.UNKNOWN_ACCESS_NOTES
            notes = notes.format(entity=entity, actions=json.dumps(actions))

        self.add_issue(10, tag, item, notes=notes)

    def record_cross_account_root(self, item, entity, actions):
        tag = Categories.CROSS_ACCOUNT_ROOT
        notes = Categories.CROSS_ACCOUNT_ROOT_NOTES.format(
            entity=entity, actions=json.dumps(actions))
        self.add_issue(6, tag, item, notes=notes)

    def record_arn_parse_issue(self, item, arn):
        tag = Categories.PARSE_ERROR
        notes = Categories.PARSE_ERROR_NOTES.format(input_type='ARN', input=arn)
        self.add_issue(3, tag, item, notes=notes)

    def add_issue(self, score, issue, item, notes=None, action_instructions=None):
        """
        Adds a new issue to an item, if not already reported.
        :return: The new issue
        """

        if notes and len(notes) > 1024:
            notes = notes[0:1024]

        if not self.override_scores:
            query = ItemAuditScore.query.filter(ItemAuditScore.technology == self.index)
            self.override_scores = query.all()

        # Check for override scores to apply
        score = self._check_for_override_score(score, item.account)

        for existing_issue in item.audit_issues:
            if existing_issue.issue == issue:
                if existing_issue.notes == notes:
                    if existing_issue.score == score:
                        app.logger.debug(
                            "Not adding issue because it was already found:{}/{}/{}/{}\n\t{} -- {}"
                            .format(item.index, item.region, item.account, item.name, issue, notes))
                        return existing_issue

        app.logger.debug("Adding issue: {}/{}/{}/{}\n\t{} -- {}"
                         .format(item.index, item.region, item.account, item.name, issue, notes))
        new_issue = datastore.ItemAudit(score=score,
                                        issue=issue,
                                        notes=notes,
                                        action_instructions=action_instructions,
                                        justified=False,
                                        justified_user_id=None,
                                        justified_date=None,
                                        justification=None)

        item.audit_issues.append(new_issue)
        return new_issue

    def prep_for_audit(self):
        """
        Subclasses must ensure this is called through super.
        """
        self._load_object_store()

    def audit_objects(self):
        """
        Inspect all of the auditor's items.
        """
        app.logger.debug("Asked to audit {} Objects".format(len(self.items)))
        self.prep_for_audit()
        self.current_support_items = {}
        query = ItemAuditScore.query.filter(ItemAuditScore.technology == self.index)
        self.override_scores = query.all()

        methods = [getattr(self, method_name) for method_name in dir(self) if method_name.find("check_") == 0]
        app.logger.debug("methods: {}".format(methods))
        for item in self.items:
            for method in methods:
                self.current_method_name = method.__name__
                # If the check function is disabled by an entry on Settings/Audit Issue Scores
                # the function will not be run and any previous issues will be cleared
                if not self._is_current_method_disabled():
                    method(item)

        self.override_scores = None

    def _is_current_method_disabled(self):
        """
        Determines whether this method has been marked as disabled based on Audit Issue Scores
        settings.
        """
        for override_score in self.override_scores:
            if override_score.method == self.current_method_name + ' (' + self.__class__.__name__ + ')':
                return override_score.disabled

        return False

    def read_previous_items(self):
        """
        Pulls the last-recorded configuration from the database.
        :return: List of all items for the given technology and the given account.
        """
        prev_list = []
        for account in self.accounts:
            prev = self.datastore.get_all_ctype_filtered(tech=self.index, account=account, include_inactive=False)
            # Returns a map of {Item: ItemRevision}
            for item in prev:
                item_revision = prev[item]
                new_item = ChangeItem(index=self.index,
                                      region=item.region,
                                      account=item.account.name,
                                      name=item.name,
                                      arn=item.arn,
                                      new_config=item_revision.config)
                new_item.audit_issues = []
                new_item.db_item = item
                prev_list.append(new_item)
        return prev_list

    def read_previous_items_for_account(self, index, account):
        """
        Pulls the last-recorded configuration from the database.
        :return: List of all items for the given technology and the given account.
        """
        prev_list = []
        prev = self.datastore.get_all_ctype_filtered(tech=index, account=account, include_inactive=False)
        # Returns a map of {Item: ItemRevision}
        for item in prev:
            item_revision = prev[item]
            new_item = ChangeItem(index=self.index,
                                  region=item.region,
                                  account=item.account.name,
                                  name=item.name,
                                  arn=item.arn,
                                  new_config=item_revision.config)
            new_item.audit_issues = []
            new_item.db_item = item
            prev_list.append(new_item)

        return prev_list

    def save_issues(self):
        """
        Save all new issues.  Delete all fixed issues.
        """
        app.logger.debug("\n\nSaving Issues.")

        # Work around for issue where previous get's may cause commit to fail
        db.session.rollback()
        for item in self.items:
            changes = False
            loaded = False

            if not hasattr(item, 'db_item') or not item.db_item.issues:
                loaded = True
                item.db_item = self.datastore._get_item(item.index, item.region, item.account, item.name)

            for issue in item.db_item.issues:
                if not issue.auditor_setting:
                    self._set_auditor_setting_for_issue(issue)

            existing_issues = {'{cls} -- {key}'.format(
                cls=issue.auditor_setting.auditor_class,
                key=issue.key()): issue for issue in list(item.db_item.issues)}

            new_issues = list(item.audit_issues)
            new_issue_keys = [issue.key() for issue in new_issues]

            # New/Regressions/Existing Issues
            for new_issue in new_issues:
                new_issue_key = '{cls} -- {key}'.format(cls=self.__class__.__name__, key=new_issue.key())

                # Make a new issue out of it:
                if new_issue_key not in existing_issues:
                    # For whatever reason... If we don't make a copy of the SQLAlchemy object, it complains that it
                    # is already attached to another item >:///
                    item.audit_issues.remove(new_issue)
                    new_issue = new_issue.copy_unlinked()
                    item.audit_issues.append(new_issue)

                    changes = True
                    app.logger.debug("Saving NEW issue {}".format(new_issue))
                    item.found_new_issue = True
                    item.confirmed_new_issues.append(new_issue)

                    new_issue.item_id = item.db_item.id
                    item.db_item.issues.append(new_issue)
                    db.session.add(new_issue)

                    continue

                existing_issue = existing_issues[new_issue_key]
                if existing_issue.fixed:
                    # regression
                    changes = True
                    existing_issue.fixed = False
                    app.logger.debug("Previous Issue has Regressed {}".format(existing_issue))

                else:
                    # existing issue
                    item.confirmed_existing_issues.append(existing_issue)

                    item_key = "{}/{}/{}/{}".format(item.index, item.region, item.account, item.name)
                    app.logger.debug("Issue was previously found. Not overwriting."
                        "\n\t{item_key}\n\t{issue}".format(
                        item_key=item_key, issue=new_issue))

            # Fixed Issues
            for _, old_issue in list(existing_issues.items()):
                old_issue_class = old_issue.auditor_setting.auditor_class
                if old_issue.fixed:
                    continue

                if old_issue_class is None or (old_issue_class == self.__class__.__name__ and old_issue.key() not in new_issue_keys):
                    changes = True
                    old_issue.fixed = True
                    db.session.add(old_issue)
                    item.confirmed_fixed_issues.append(old_issue)
                    app.logger.debug("Marking issue as FIXED {}".format(old_issue))

            if changes:
                db.session.add(item.db_item)
            else:
                if loaded:
                    db.session.expunge(item.db_item)

        db.session.commit()
        self._create_auditor_settings()
        report_auditor_changes(self)

    def email_report(self, report):
        """
        Given a report, send an email using SES.
        """
        if not report:
            app.logger.info("No Audit issues.  Not sending audit email.")
            return

        if app.config.get("DISABLE_EMAILS"):
            app.logger.info("Emails are disabled in the Security Monkey configuration. Not sending them.")
            return

        subject = "Security Monkey {} Auditor Report".format(self.i_am_singular)
        send_email(subject=subject, recipients=self.emails, html=report)

    def create_report(self):
        """
        Using a Jinja template (jinja_audit_email.html), create a report that can be emailed.
        :return: HTML - The output of the rendered template.
        """
        jenv = get_jinja_env()
        template = jenv.get_template('jinja_audit_email.html')

        for item in self.items:
            item.reportable_issues = list()
            item.score = 0
            for issue in item.db_item.issues:
                if issue.fixed or issue.auditor_setting.disabled:
                    continue
                if not app.config.get('EMAIL_AUDIT_REPORTS_INCLUDE_JUSTIFIED', True) and issue.justified:
                    continue
                item.reportable_issues.append(issue)
                item.score += issue.score

        sorted_list = sorted(self.items, key=lambda item: item.score, reverse=True)
        report_list = [item for item in sorted_list if (item.score) ]

        if report_list:
            return template.render({'items': report_list})
        return False

    def applies_to_account(self, account):
        """
        Placeholder for custom auditors which may only want to run against
        certain types of accounts
        """
        return True

    def _create_auditor_settings(self):
        """
        Checks to see if an AuditorSettings entry exists for each issue.
        If it does not, one will be created with disabled set to false.
        """
        app.logger.debug("Creating/Assigning Auditor Settings in account {} and tech {}".format(self.accounts, self.index))

        query = ItemAudit.query
        query = query.join((Item, Item.id == ItemAudit.item_id))
        query = query.join((Technology, Technology.id == Item.tech_id))
        query = query.filter(Technology.name == self.index)
        issues = query.filter(ItemAudit.auditor_setting_id == None).all()

        for issue in issues:
            self._set_auditor_setting_for_issue(issue)

        db.session.commit()
        app.logger.debug("Done Creating/Assigning Auditor Settings in account {} and tech {}".format(self.accounts, self.index))

    def _set_auditor_setting_for_issue(self, issue):

        auditor_setting = AuditorSettings.query.filter(
            and_(
                # TODO: This MUST be modified when switching to new issue logic in future:
                #       Currently there should be exactly 1 item in the list of sub_items:
                AuditorSettings.tech_id == issue.item.tech_id,
                AuditorSettings.account_id == issue.item.account_id,
                AuditorSettings.issue_text == issue.issue,
                AuditorSettings.auditor_class == self.__class__.__name__
            )
        ).first()

        if auditor_setting:
            auditor_setting.issues.append(issue)
            db.session.add(auditor_setting)
            return auditor_setting

        auditor_setting = AuditorSettings(
            # TODO: This MUST be modified when switching to new issue logic in future:
            #       Currently there should be exactly 1 item in the list of sub_items:
            tech_id=issue.item.tech_id,
            account_id=issue.item.account_id,
            disabled=False,
            issue_text=issue.issue,
            auditor_class=self.__class__.__name__
        )

        auditor_setting.issues.append(issue)
        db.session.add(auditor_setting)
        db.session.commit()
        db.session.refresh(auditor_setting)

        app.logger.debug("Created AuditorSetting: {} - {} - {}".format(
            issue.issue,
            self.index,
            # TODO: This MUST be modified when switching to new issue logic in future:
            #       Currently there should be exactly 1 item in the list of sub_items:
            issue.item.account.name))

        return auditor_setting

    def get_auditor_support_items(self, auditor_index, account):
        for index in self.support_auditor_indexes:
            if index == auditor_index:
                audited_items = self.current_support_items.get(account + auditor_index)
                if audited_items is None:
                    audited_items = self.read_previous_items_for_account(auditor_index, account)
                    if not audited_items:
                        app.logger.info("{} Could not load audited items for {}/{}".format(self.index, auditor_index, account))
                        self.current_support_items[account+auditor_index] = []
                    else:
                        self.current_support_items[account+auditor_index] = audited_items
                return audited_items

        raise Exception("Auditor {} is not configured as an audit support auditor for {}".format(auditor_index, self.index))

    def get_watcher_support_items(self, watcher_index, account):
        for index in self.support_watcher_indexes:
            if index == watcher_index:
                items = self.current_support_items.get(account + watcher_index)
                if items is None:
                    items = self.read_previous_items_for_account(watcher_index, account)
                    # Only the item contents should be used for watcher support
                    # config. This prevents potentially stale issues from being
                    # used by the auditor
                    for item in items:
                        item.db_item.issues = []

                    if not items:
                        app.logger.info("{} Could not load support items for {}/{}".format(self.index, watcher_index, account))
                        self.current_support_items[account+watcher_index] = []
                    else:
                        self.current_support_items[account+watcher_index] = items
                return items

        raise Exception("Watcher {} is not configured as a data support watcher for {}".format(watcher_index, self.index))

    def _sum_item_score(self, score, issue, matching_issue):
        if not score:
            total = issue.score + matching_issue.score
        else:
            total = score

        # 999999 is the maximum number a score can be -- this prevents DB integer out of range exceptions
        if total > 999999:
            return 999999

        return total

    def link_to_support_item_issues(self, item, sub_item, sub_issue_message=None, issue_message=None, issue=None, score=None):
        """
        Creates a new issue that is linked to an issue in a support auditor
        """
        matching_issues = []
        for sub_issue in sub_item.issues:
            if sub_issue.fixed:
                continue
            if not sub_issue_message or sub_issue.issue == sub_issue_message:
                matching_issues.append(sub_issue)

        for matching_issue in matching_issues:
            if issue:
                issue.score = self._sum_item_score(score, issue, matching_issue)
            else:
                issue_message = issue_message or sub_issue_message or 'UNDEFINED'
                link_score = score or matching_issue.score
                issue = self.add_issue(link_score, issue_message, item)

        if issue:
            issue.sub_items.append(sub_item)

    def link_to_support_item(self, score, issue_message, item, sub_item, issue=None):
        """
        Creates a new issue that is linked a support watcher item
        """
        if issue is None:
            issue = self.add_issue(score, issue_message, item)
        issue.sub_items.append(sub_item)
        return issue

    def _check_for_override_score(self, score, account):
        """
        Return an override to the hard coded score for an issue being added. This could either
        be a general override score for this check method or one that is specific to a particular
        field in the account.

        :param score: the hard coded score which will be returned back if there is
               no applicable override
        :param account: The account name, used to look up the value of any pattern
               based overrides
        :return:
        """
        for override_score in self.override_scores:
            # Look for an oberride entry that applies to
            if override_score.method == self.current_method_name + ' (' + self.__class__.__name__ + ')':
                # Check for account pattern override where a field in the account matches
                # one configured in Settings/Audit Issue Scores
                account = get_account_by_name(account)
                for account_pattern_score in override_score.account_pattern_scores:
                    if getattr(account, account_pattern_score.account_field, None):
                        # Standard account field, such as identifier or notes
                        account_pattern_value = getattr(account, account_pattern_score.account_field)
                    else:
                        # If there is no attribute, this is an account custom field
                        account_pattern_value = account.getCustom(account_pattern_score.account_field)

                    if account_pattern_value is not None:
                        # Override the score based on the matching pattern
                        if account_pattern_value == account_pattern_score.account_pattern:
                            app.logger.debug("Overriding score based on config {}:{} {}/{}".format(self.index, self.current_method_name + '(' + self.__class__.__name__ + ')', score, account_pattern_score.score))
                            score = account_pattern_score.score
                            break
                else:
                    # No specific override pattern fund. use the generic override score
                    app.logger.debug("Overriding score based on config {}:{} {}/{}".format(self.index, self.current_method_name + '(' + self.__class__.__name__ + ')', score, override_score.score))
                    score = override_score.score

        return score
