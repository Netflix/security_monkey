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
.. module: security_monkey.watchers.elb
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

from boto.ec2.elb import regions


def parse_policy(policy):
    ret = {}
    ret['name'] = policy['name']
    ret['type'] = policy['type']
    attrs = policy['Attributes']

    if policy['type'] != 'SSLNegotiationPolicyType':
        return ret

    ret['sslv2'] = attrs['Protocol-SSLv2']
    ret['sslv3'] = attrs['Protocol-SSLv3']
    ret['tlsv1'] = attrs['Protocol-TLSv1']
    ret['tlsv1_1'] = attrs['Protocol-TLSv1.1']
    ret['tlsv1_2'] = attrs['Protocol-TLSv1.2']
    ret['server_defined_cipher_order'] = attrs['Server-Defined-Cipher-Order']
    ret['reference_security_policy'] = attrs.get('Reference-Security-Policy', None)

    non_ciphers = [
        'Server-Defined-Cipher-Order',
        'Protocol-SSLv2',
        'Protocol-SSLv3',
        'Protocol-TLSv1',
        'Protocol-TLSv1.1',
        'Protocol-TLSv1.2',
        'Reference-Security-Policy'
    ]

    ciphers = []
    for cipher in attrs:
        if attrs[cipher] and cipher not in non_ciphers:
            ciphers.append(cipher)

    ciphers.sort()
    ret['supported_ciphers'] = ciphers

    return ret


class ELB(Watcher):
    index = 'elb'
    i_am_singular = 'ELB'
    i_am_plural = 'ELBs'

    def __init__(self, accounts=None, debug=False):
        super(ELB, self).__init__(accounts=accounts, debug=debug)

    def _setup_botocore(self, account):
        from security_monkey.common.sts_connect import connect
        self.botocore_session = connect(account, 'botocore')
        self.botocore_elb = self.botocore_session.get_service('elb')
        self.botocore_operation = self.botocore_elb.get_operation('describe-load-balancer-policies')

    def _get_listener_policies(self, elb, endpoint):
        http_response, response_data = self.botocore_operation.call(endpoint, load_balancer_name=elb.name)
        policies = {}
        for policy in response_data.get('PolicyDescriptions', []):
            p = {"name": policy['PolicyName'], "type": policy['PolicyTypeName'], "Attributes": {}}
            for attribute in policy['PolicyAttributeDescriptions']:
                if attribute['AttributeValue'] == "true":
                    p['Attributes'][attribute['AttributeName']] = True
                elif attribute['AttributeValue'] == "false":
                    p['Attributes'][attribute['AttributeName']] = False
                else:
                    p['Attributes'][attribute['AttributeName']] = attribute['AttributeValue']

            # This next bit may overwrite anything you did in the above for-loop:
            if "Reference-Security-Policy" in p['Attributes']:
                p['reference_security_policy'] = p['Attributes']['Reference-Security-Policy']
                del p['Attributes']
            else:
                p = parse_policy(p)

            policies[policy['PolicyName']] = p

        return policies

    def slurp(self):
        """
        :returns: item_list - list of ELB's.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()
        from security_monkey.common.sts_connect import connect
        item_list = []
        exception_map = {}
        for account in self.accounts:
            self._setup_botocore(account)
            for region in regions():
                app.logger.debug("Checking {}/{}/{}".format(self.index, account, region.name))
                elb_conn = connect(account, 'elb', region=region.name)
                botocore_endpoint = self.botocore_elb.get_endpoint(region.name)

                try:
                    all_elbs = []
                    marker = None

                    while True:
                        response = self.wrap_aws_rate_limited_call(
                            elb_conn.get_all_load_balancers,
                            marker=marker
                        )

                        # build our elb list
                        all_elbs.extend(response)

                        # ensure that we get every elb
                        if response.next_marker:
                            marker = response.next_marker
                        else:
                            break

                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), self.index, account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map)
                    continue

                app.logger.debug("Found {} {}".format(len(all_elbs), self.i_am_plural))
                for elb in all_elbs:

                    if self.check_ignore_list(elb.name):
                        continue

                    elb_map = {}
                    elb_map['availability_zones'] = list(elb.availability_zones)
                    elb_map['canonical_hosted_zone_name'] = elb.canonical_hosted_zone_name
                    elb_map['canonical_hosted_zone_name_id'] = elb.canonical_hosted_zone_name_id
                    elb_map['dns_name'] = elb.dns_name
                    elb_map['health_check'] = {'target': elb.health_check.target, 'interval': elb.health_check.interval}
                    elb_map['is_cross_zone_load_balancing'] = self.wrap_aws_rate_limited_call(
                        elb.is_cross_zone_load_balancing
                    )
                    elb_map['scheme'] = elb.scheme
                    elb_map['security_groups'] = list(elb.security_groups)
                    elb_map['source_security_group'] = elb.source_security_group.name
                    elb_map['subnets'] = list(elb.subnets)
                    elb_map['vpc_id'] = elb.vpc_id

                    backends = []
                    for be in elb.backends:
                        backend = {}
                        backend['instance_port'] = be.instance_port
                        policies = []
                        for bepol in be.policies:
                            policies.append(bepol.policy_name)
                        backend['policies'] = policies
                        backends.append(backend)
                    elb_map['backends'] = backends

                    elb_policies = self._get_listener_policies(elb, botocore_endpoint)
                    listeners = []
                    for li in elb.listeners:
                        listener = {
                            'load_balancer_port': li.load_balancer_port,
                            'instance_port': li.instance_port,
                            'protocol': li.protocol,
                            'instance_protocol': li.instance_protocol,
                            'ssl_certificate_id': li.ssl_certificate_id,
                            'policies': [elb_policies[policy_name] for policy_name in li.policy_names]
                        }
                        listeners.append(listener)
                    elb_map['listeners'] = listeners

                    policies = {}
                    app_cookie_stickiness_policies = []
                    for policy in elb.policies.app_cookie_stickiness_policies:
                        app_cookie_stickiness_policy = {}
                        app_cookie_stickiness_policy['policy_name'] = policy.policy_name
                        app_cookie_stickiness_policy['cookie_name'] = policy.cookie_name
                        app_cookie_stickiness_policies.append(app_cookie_stickiness_policy)
                    policies['app_cookie_stickiness_policies'] = app_cookie_stickiness_policies

                    lb_cookie_stickiness_policies = []
                    for policy in elb.policies.lb_cookie_stickiness_policies:
                        lb_cookie_stickiness_policy = {}
                        lb_cookie_stickiness_policy['policy_name'] = policy.policy_name
                        lb_cookie_stickiness_policy['cookie_expiration_period'] = policy.cookie_expiration_period
                        lb_cookie_stickiness_policies.append(lb_cookie_stickiness_policy)
                    policies['lb_cookie_stickiness_policies'] = lb_cookie_stickiness_policies

                    policies['other_policies'] = []
                    for opol in elb.policies.other_policies:
                        policies['other_policies'].append(opol.policy_name)
                    elb_map['policies'] = policies

                    item = ELBItem(region=region.name, account=account, name=elb.name, config=elb_map)
                    item_list.append(item)

        return item_list, exception_map


class ELBItem(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config={}):
        super(ELBItem, self).__init__(
            index=ELB.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
