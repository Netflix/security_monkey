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
.. module: security_monkey.alerters.custom_alerter
    :platform: Unix

.. version:: $$VERSION$$
.. moduleauthor:: Bridgewater OSS <opensource@bwater.com>


"""
from security_monkey import app

alerter_registry = {}


class AlerterType(type):

    def __init__(cls, name, bases, attrs):
        if getattr(cls, "report_auditor_changes", None) and getattr(cls, "report_watcher_changes", None):
            app.logger.debug("Registering alerter %s", cls.__name__)
            if cls.__name__ not in alerter_registry.keys():
                alerter_registry.update({cls.__name__: cls})


def report_auditor_changes(auditor):
    app.logger.info(vars(auditor))
    for alerter_class in alerter_registry.keys():
        alerter = alerter_registry.get(alerter_class)()
        alerter.report_auditor_changes(auditor)


def report_watcher_changes(watcher):
    app.logger.info(vars(watcher))
    for alerter_class in alerter_registry.keys():
        alerter = alerter_registry.get(alerter_class)()
        alerter.report_watcher_changes(watcher)
