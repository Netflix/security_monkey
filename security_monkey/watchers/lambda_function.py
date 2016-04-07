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


"""
from security_monkey.decorators import record_exception, iter_account_region
from security_monkey.watcher import Watcher
from security_monkey.watcher import ChangeItem
from security_monkey import app


def lambda_function_name(lambda_function):
    return lambda_function.get('FunctionName') + ' (' + lambda_function.get('FunctionArn') + ')'


class LambdaFunction(Watcher):
    index = 'lambda'
    i_am_singular = 'Lambda Function'
    i_am_plural = 'Lambda Functions'

    def __init__(self, accounts=None, debug=False):
        super(LambdaFunction, self).__init__(accounts=accounts, debug=debug)

    @record_exception()
    def list_functions(self, **kwargs):
        from security_monkey.common.sts_connect import connect
        app.logger.debug("Checking {}/{}/{}".format(self.index,
                                                    kwargs['account_name'], kwargs['region']))
        lambda_client = connect(kwargs['account_name'], 'boto3.lambda.client',
                                region=kwargs['region'],
                                assumed_role=kwargs['assumed_role'])

        response = self.wrap_aws_rate_limited_call(
            lambda_client.list_functions
        )
        lambda_functions = response.get('Functions')
        return lambda_functions

    def slurp(self):
        """
        :returns: item_list - list of Lambda functions.
        :returns: exception_map - A dict where the keys are a tuple containing the
            location of the exception and the value is the actual exception

        """
        self.prep_for_slurp()

        @iter_account_region(index=self.index, accounts=self.accounts, service_name='lambda')
        def slurp_items(**kwargs):
            item_list = []
            exception_map = {}
            kwargs['exception_map'] = exception_map
            lambda_functions = self.list_functions(**kwargs)

            if lambda_functions:
                app.logger.debug("Found {} {}".format(
                    len(lambda_functions), self.i_am_plural))
                for lambda_function in lambda_functions:
                    name = lambda_function_name(lambda_function)

                    if self.check_ignore_list(name):
                        continue

                    config = {
                        'function_name': lambda_function.get('FunctionName'),
                        'function_arn': lambda_function.get('FunctionArn'),
                        'runtime': lambda_function.get('Runtime'),
                        'role': lambda_function.get('Role'),
                        'handler': lambda_function.get('Handler'),
                        'code_size': lambda_function.get('CodeSize'),
                        'description': lambda_function.get('Description'),
                        'timeout': lambda_function.get('Timeout'),
                        'memory_size': lambda_function.get('MemorySize'),
                        'last_modified': lambda_function.get('LastModified'),
                        'code_sha256': lambda_function.get('CodeSha256'),
                        'version': lambda_function.get('Version'),
                        'vpc_config': lambda_function.get('VpcConfig')
                    }

                    item = LambdaFunctionItem(region=kwargs['region'],
                                              account=kwargs['account_name'],
                                              name=name, config=dict(config))

                    item_list.append(item)

            return item_list, exception_map
        return slurp_items()


class LambdaFunctionItem(ChangeItem):

    def __init__(self, region=None, account=None, name=None, config={}):
        super(LambdaFunctionItem, self).__init__(
            index=LambdaFunction.index,
            region=region,
            account=account,
            name=name,
            new_config=config)
