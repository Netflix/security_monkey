#     Copyright 2016 Bridgewater Associates
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
.. module: security_monkey.watchers.lambda_function
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>
.. moduleauthor:: Patrick Kelley <patrick@netflix.com>

"""
from security_monkey.cloudaux_watcher import CloudAuxWatcher
from cloudaux.aws.lambda_function import list_functions
from cloudaux.orchestration.aws.lambda_function import get_lambda_function


class LambdaFunction(CloudAuxWatcher):
    index = 'lambda'
    i_am_singular = 'Lambda Function'
    i_am_plural = 'Lambda Functions'
    service_name = 'lambda'

    def get_name_from_list_output(self, item):
        return item['FunctionName']

    def list_method(self, **kwargs):
        return list_functions(**kwargs)

    def get_method(self, item, **kwargs):
        return get_lambda_function(item, **kwargs)

