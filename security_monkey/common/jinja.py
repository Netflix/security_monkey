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
.. module: security_onkey.common.jinja
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

import os.path
import jinja2

templates = "templates"


def get_jinja_env():
    """
    Returns a Jinja environment with a FileSystemLoader for our templates
    """
    directory = os.path.abspath('security_monkey')
    templates_directory = os.path.join(directory, templates)
    jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_directory))
    #jinja_environment.filters['dateformat'] = dateformat
    return jinja_environment
