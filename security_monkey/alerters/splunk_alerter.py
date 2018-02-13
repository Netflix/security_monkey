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
from security_monkey.datastore import SplunkAlerter
from security_monkey.alerters.custom_alerter import alerter_registry, AlerterType
from security_monkey.exceptions import SplunkAlerterExists
from security_monkey import db
from security_monkey import app

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import json
import time
import socket
import threading
import Queue
import uuid

__author__ = "george@georgestarcher.com (George Starcher)"

# Default batch max size to match splunk's default limits for max byte
# See http_input stanza in limits.conf; note in testing I had to limit to 100,000 to avoid http event collector breaking connection
# Auto flush will occur if next event payload will exceed limit
_max_content_bytes = 100000
_number_of_threads = 10


# An improved requests retry method from
# https://www.peterbe.com/plog/best-practice-with-retries-with-requests

def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None):
    session = session or requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class http_event_collector:

    def __init__(self, token, http_event_server, input_type='json', host="", http_event_port='8088',
                 http_event_server_ssl=True, max_bytes=_max_content_bytes, http_event_collector_debug=False,
                 http_event_collector_SSL_verify=False):
        self.token = token
        self.http_event_collector_debug = http_event_collector_debug
        self.http_event_collector_SSL_verify = http_event_collector_SSL_verify
        self.batchEvents = []
        self.maxByteLength = max_bytes
        self.currentByteLength = 0
        self.input_type = input_type
        self.flushQueue = Queue.Queue(0)
        for x in range(_number_of_threads):
            t = threading.Thread(target=self.batchThread)
            t.daemon = True
            t.start()

        if self.http_event_collector_SSL_verify == False:
            requests.packages.urllib3.disable_warnings()

        # Set host to specified value or default to localhostname if no value provided
        if host:
            self.host = host
        else:
            self.host = socket.gethostname()

        # Build and set server_uri for http event collector
        # Defaults to SSL if flag not passed
        # Defaults to port 8088 if port not passed

        if http_event_server_ssl:
            protocol = 'https'
        else:
            protocol = 'http'

        if input_type == 'raw':
            input_url = '/raw?channel=' + str(uuid.uuid1())
        else:
            input_url = '/event'

        self.server_uri = '%s://%s:%s/services/collector%s' % (protocol, http_event_server, http_event_port, input_url)

        if self.http_event_collector_debug:
            print self.token
            print self.server_uri
            print self.input_type

    def sendEvent(self, payload, eventtime=""):
        # Method to immediately send an event to the http event collector

        headers = {'Authorization': 'Splunk ' + self.token}

        if self.input_type == 'json':
            # If eventtime in epoch not passed as optional argument and not in payload, use current system time in epoch
            if not eventtime and 'time' not in payload:
                eventtime = str(int(time.time()))
                payload.update({'time': eventtime})

            # Fill in local hostname if not manually populated
            if 'host' not in payload:
                payload.update({"host": self.host})

        # send event to http event collector
        event = []
        if self.input_type == 'json':
            event.append(json.dumps(payload))
        else:
            event.append(str(payload))

        self.flushQueue.put(event)
        if self.http_event_collector_debug:
            print "Single Submit: Sticking the event on the queue."
            print event
        self.waitUntilDone()

    def batchEvent(self, payload, eventtime=""):
        # Method to store the event in a batch to flush later

        if self.input_type == 'json':
            # Fill in local hostname if not manually populated
            if 'host' not in payload:
                payload.update({"host": self.host})

            # If eventtime in epoch not passed as optional argument and not in payload, use current system time in epoch
            if not eventtime and 'time' not in payload:
                eventtime = str(int(time.time()))
                payload.update({"time": eventtime})

            payloadString = json.dumps(payload)

        else:
            payloadString = str(payload)
            if not payloadString.endswith("\n"):
                payloadString = payloadString + "\n"

        payloadLength = len(payloadString)

        if ((self.currentByteLength + payloadLength) > self.maxByteLength or (
                self.maxByteLength - self.currentByteLength) < payloadLength):
            if self.http_event_collector_debug:
                print "Auto Flush: Sticking the batch on the queue."
            self.flushQueue.put(self.batchEvents)
            self.batchEvents = []
            self.currentByteLength = 0

        self.batchEvents.append(payloadString)
        self.currentByteLength += payloadLength

    def batchThread(self):
        # Threads to send batches of events.

        while True:
            if self.http_event_collector_debug:
                print "Events received on thread. Sending to Splunk."
            payload = " ".join(self.flushQueue.get())
            headers = {'Authorization': 'Splunk ' + self.token}
            # try to post payload twice then give up and move on
            try:
                r = requests_retry_session().post(self.server_uri, data=payload, headers=headers,
                                                  verify=self.http_event_collector_SSL_verify)
            except Exception as e:
                pass

            if self.http_event_collector_debug:
                print r.text
            self.flushQueue.task_done()

    def waitUntilDone(self):
        # Block until all flushQueue is empty.
        self.flushQueue.join()
        return

    def flushBatch(self):
        if self.http_event_collector_debug:
            print "Manual Flush: Sticking the batch on the queue."
        self.flushQueue.put(self.batchEvents)
        self.batchEvents = []
        self.currentByteLength = 0
        self.waitUntilDone()

class SplunkHECAlerter(object):
    __metaclass__ = AlerterType
    account_type = None
    compatable_account_types = []
    custom_field_configs = []
    identifier_label = None
    identifier_tool_tip = None
    hecs = None

    def create_hec(self):
        if self.hecs is not None:
            return
        alerters = SplunkAlerter.query.filter(SplunkAlerter.active == True).all()
        self.hecs = []
        for alerter in alerters:
            hec = http_event_collector(token=alerter.token, http_event_port=alerter.token, http_event_server=alerter.host)
            self.hecs.append(hec)

    def handle_events(self, events, caller):
        self.create_hec()
        for hec in self.hecs:
            payload = {}
            payload.update({"sourcetype": "securitymonkey:{}".format(caller)})
            payload.update({"source": "secdev"})
            payload.update({"host": "secdev.ubi.com"})
            for event in events:
                payload.update({"event":event})
                app.logger.warn("Will send {}".format(event))
                hec.batchEvent(payload)
        for hec in self.hecs:
            hec.flushBatch()


    def report_watcher_changes(self, watch):
        events = []
        for item in watch.created_items:
            event = {
                "action": "item",
                "status": "create",
                "id": item.db_item.id,
                "resource": item.index,
                "account": item.account,
                "region": item.region,
                "name": item.name
            }
            events.append(event)

        for item in watch.changed_items:
            event = {
                "action": "item",
                "status": "change",
                "id": item.db_item.id,
                "resource": item.index,
                "account": item.account,
                "region": item.region,
                "name": item.name
            }
            events.append(event)

        for item in watch.deleted_items:
            event = {
                "action": "item",
                "status": "delete",
                "id": item.db_item.id,
                "resource": item.index,
                "account": item.account,
                "region": item.region,
                "name": item.name
            }
            events.append(event)
        if len(events) > 0:
            self.handle_events(events, "watch")

    def report_auditor_changes(self, auditor):
        events = []
        for item in auditor.items:
            for issue in item.confirmed_new_issues:
                event = {
                    "action": "issue",
                    "status":"create",
                    "id" : issue.id,
                    "resource":item.index,
                    "account":item.account,
                    "region":item.region,
                    "name": item.name,
                    "issue":issue.issue
                }
                events.append(event)

            for issue in item.confirmed_fixed_issues:
                event = {
                    "action": "issue",
                    "status":"fix",
                    "id": issue.id,
                    "resource": item.index,
                    "account": item.account,
                    "region": item.region,
                    "name": item.name,
                    "issue": issue.issue
                }
                events.append(event)
        if len(events) > 0:
            self.handle_events(events, "auditor")

    def add(self, alerter_id, host, port, token, active):
        alerters = SplunkAlerter.query.filter(SplunkAlerter.host == host).filter(SplunkAlerter.port == port).all()
        if len(alerters) >= 1 and alerters[0].id != alerter_id:
            raise SplunkAlerterExists(host, port)
        alerter = SplunkAlerter.query.filter(SplunkAlerter.id == alerter_id).one()
        alerter.host = host
        alerter.port = port
        alerter.token = token
        alerter.active = active
        alerter.validate()
        db.session.add(alerter)
        db.session.commit()
        db.session.refresh(alerter)
        return alerter

    def create(self, host, port, token, active):
        alerters = SplunkAlerter.query.filter(SplunkAlerter.host == host).filter(SplunkAlerter.port == port).all()
        if len(alerters) >= 1:
            raise SplunkAlerterExists(host, port)
        alerter = SplunkAlerter()
        alerter.host = host
        alerter.port = port
        alerter.token = token
        alerter.active = active
        alerter.validate()

        db.session.add(alerter)
        db.session.commit()
        db.session.refresh(alerter)
        return alerter

