#     Copyright 2014 Yelp, Inc.
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
.. module: security_monkey.watchers.redshift
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Ivan Leichtling <ivanlei@yelp.com> @c0wl

"""

from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey.constants import TROUBLE_REGIONS
from security_monkey.exceptions import InvalidAWSJSON
from security_monkey.exceptions import BotoConnectionIssue
from security_monkey import app

import json
import boto
from boto.redshift import regions


class Redshift(Watcher):
    index = 'redshift'
    i_am_singular = 'Redshift Cluster'
    i_am_plural = 'Redshift Clusters'

    def __init__(self, accounts=None, debug=False):
        super(Redshift, self).__init__(accounts=accounts, debug=debug)

    def slurp(self):
        """
        :returns: item_list - list of Redshift Policies.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()
        from security_monkey.common.sts_connect import connect
        item_list = []
        exception_map = {}
        for account in self.accounts:
            for region in regions():
                app.logger.debug("Checking {}/{}/{}".format(self.index, account, region.name))
                try:
                    redshift = connect(account, 'redshift', region=region)
                    response = self.wrap_aws_rate_limited_call(
                        redshift.describe_clusters
                    )
                    all_clusters = response['DescribeClustersResponse']['DescribeClustersResult']['Clusters']
                except Exception as e:
                    if region.name not in TROUBLE_REGIONS:
                        exc = BotoConnectionIssue(str(e), 'redshift', account, region.name)
                        self.slurp_exception((self.index, account, region.name), exc, exception_map)
                    continue
                app.logger.debug("Found {} {}".format(len(all_clusters), Redshift.i_am_plural))
                for cluster in all_clusters:
                    cluster_id = cluster['ClusterIdentifier']
                    if self.check_ignore_list(cluster_id):
                        continue

                    try:
                        item = RedshiftCluster(region=region.name, account=account, name=cluster_id, config=cluster)
                        item_list.append(item)
                    except:
                        import pudb; pudb.set_trace()
                        self.slurp_exception((self.index, account, region, cluster_id), InvalidAWSJSON(json_str), exception_map)
        return item_list, exception_map


class RedshiftCluster(ChangeItem):
    def __init__(self, region=None, account=None, name=None, config={}):
        super(RedshiftCluster, self).__init__(
            index=Redshift.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
