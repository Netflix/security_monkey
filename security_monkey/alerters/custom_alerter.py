#     Copyright 2018 Willowtree Inc
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
.. version:: SlackBot Integration Alerter w/ Security_Monkey
.. moduleauthor:: Drew Gallis <drew.gallis@willowtreeapps.com>
"""
from security_monkey import app
from slack_post import postMessage
import os

alerter_registry = []

class AlerterType(type):
    print(os.environ) #remove if you don't need to check your env for your slack api token
    def __init__(self, cls, name, bases, attrs):
        if getattr(cls, "report_auditor_changes", None) and getattr(cls, "report_watcher_changes", None):
            app.logger.debug("Registering alerter %s", cls.__name__)
            alerter_registry.append(cls)


def report_auditor_changes(auditor):
       for item in auditor.items:
            for issue in item.confirmed_new_issues:
                # Create a text output of your auditor new issue in scope
                attachment = "ID: {!s}\n Index: {!s}\n Account: {!s}\n Region: {!s}\n Name: {!s}\n Issue: {!s}".format(issue.id, item.index, item.account, item.region, item.name, issue.issue)
                print("attachment: " + attachment)
                postMessage(attachment, "Auditor - Reporting on Issue Created", item.index, item.name) 
            for issue in item.confirmed_fixed_issues:
                # Create a text output of your auditor fixed issue in scope
                attachment = "ID: {!s}\n Index: {!s}\n Account: {!s}\n Region: {!s}\n Name: {!s}\n Issue: {!s}".format(issue.id, item.index, item.account, item.region, item.name, issue.issue)
                print("attachment: " + attachment)
                postMessage(attachment, "Auditor - Reporting on Issue Fixed", item.index, item.name) 

def report_watcher_changes(watcher):
    print(watcher.created_items)
    for item in watcher.created_items:
        attachment = "Index: {!s}\n Account: {!s}\n Region: {!s}\n Name: {!s}".format(item.index, item.account, item.region, item.name)
        print("attachment: " + attachment)
        postMessage(attachment, "Watcher - Created Items", item.index, item.name) 

    print(watcher.deleted_items)
    for item in watcher.deleted_items:
        attachment = "Index: {!s}\n Account: {!s}\n Region: {!s}\n Name: {!s}".format(item.index, item.account, item.region, item.name)
        print("attachment: " + attachment)
        postMessage(attachment, "Watcher - Deleted Items", item.index, item.name) 

    print(watcher.changed_items)
    for item in watcher.changed_items:
        attachment = "Index: {!s}\n Account: {!s}\n Region: {!s}\n Name: {!s}".format(item.index, item.account, item.region, item.name)
        print("attachment: " + attachment)
        postMessage(attachment, "Watcher - Changed Items", item.index, item.name)  

