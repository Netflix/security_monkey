#     Copyright 2018 Netflix, Inc.
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
.. module: security_monkey.utils
    :platform: Unix
.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>
"""
import os
from os.path import dirname, join, isfile


def resolve_app_config_path():
    """If SECURITY_MONKEY_SETTINGS is set, then use that.

    Otherwise, use env-config/config.py

    :return:
    """
    if os.environ.get('SECURITY_MONKEY_SETTINGS'):
        path = os.environ['SECURITY_MONKEY_SETTINGS']
    else:
        # find env-config/config.py
        path = dirname(dirname(__file__))
        path = join(path, 'env-config')
        path = join(path, 'config.py')

    if isfile(path):
        return path
    else:
        print('[X] PLEASE SET A CONFIG FILE WITH SECURITY_MONKEY_SETTINGS OR PUT ONE AT env-config/config.py')
        exit(-1)
