from __future__ import print_function
from security_monkey.tests import SecurityMonkeyTestCase
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from security_monkey.plugin import plugin_registry
from security_monkey import db
from security_monkey.datastore import Account, AccountType

import uuid
import json
import requests
from threading import Thread
import sys

from security_monkey.watchers.route53 import Route53
from security_monkey.auditors.elb import ELBAuditor


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


GLOBAL_TEST_TOKEN = uuid.uuid4()


class SimpleSplunkHTTP(HTTPServer, Thread):
    def __init__(self, http_bind, http_handler):
        HTTPServer.__init__(self, http_bind, http_handler)
        Thread.__init__(self)
        self.should_stop = False

    def run(self):
        while not self.should_stop:
            self.serve_forever()


class SimpleSplunkHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write("""{"text":"The requested URL was not found on this server.","code":404}""")
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')

    def do_POST(self):
        global GLOBAL_TEST_TOKEN
        if self.path != "/services/collector/event":
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.wfile.write("""{"text":"The requested URL was not found on this server.","code":404}""")
        else:
            if "authorization" not in self.headers.dict:
                self.send_response(403)
                self.send_header('Content-type', 'application/json')
                self.wfile.write("""{"text":"Invalid token","code":4}""")
                return
            token = self.headers.dict["authorization"].split(" ")
            if token[0] != "Splunk":
                self.send_response(403)
                self.send_header('Content-type', 'application/json')
                self.wfile.write("""{"text":"Invalid token","code":4}""")
                return
            if token[1] != GLOBAL_TEST_TOKEN:
                self.send_response(403)
                self.send_header('Content-type', 'application/json')
                self.wfile.write("""{"text":"Invalid token","code":4}""")
                return
            else:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                try:
                    post_data = json.loads(post_data)
                except ValueError:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write("""{"text":"Invalid data format","code":6,"invalid-event-number":1}""")
                    return
                if "event" not in post_data:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write("""{"text":"Event field is required","code":12,"invalid-event-number":0}""")
                    return
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write("""{"text":"Success","code":0}""")
                    return


class SplunkAlerterTestCase(SecurityMonkeyTestCase):
    http_thread = None

    @classmethod
    def setUpClass(cls):
        if cls.http_thread is None:
            cls.http_thread = SimpleSplunkHTTP(("127.0.0.1", 8088), SimpleSplunkHandler)
            cls.http_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http_thread.should_stop = True
        cls.http_thread.shutdown()
        cls.http_thread.server_close()
        cls.http_thread.join()

    def pre_test_setup(self):
        global GLOBAL_TEST_TOKEN
        GLOBAL_TEST_TOKEN = str(uuid.uuid4())
        from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SplunkAlerterPlugin
        self.plugin = SplunkAlerterPlugin()

    def test_intern_check_pre_test(self):
        global GLOBAL_TEST_TOKEN
        """
            Intern tets to make sure simple http server is correctly set to mimic Splunk HEC
        """
        status = requests.get("http://localhost:8088").status_code
        status = int(status)
        self.assertEqual(first=status, second=404, msg="GET requests should have 404 error but has {}".format(status))

        status = requests.get("http://localhost:8088/services/collector/event").status_code
        status = int(status)
        self.assertEqual(first=status, second=404,
                         msg="GET requests on * should have 404 error but has {}".format(status))

        status = requests.post("http://localhost:8088/").status_code
        status = int(status)
        self.assertEqual(first=status, second=404,
                         msg="POST requests on root should have 404 error but has {}".format(status))

        status = requests.post("http://localhost:8088/services/collector/event").status_code
        status = int(status)
        self.assertEqual(first=status, second=403,
                         msg="POST requests without authorization header should have 403 error but has {}".format(
                             status))

        status = requests.post("http://localhost:8088/services/collector/event",
                               headers={"authorization": "Test {}".format(GLOBAL_TEST_TOKEN)}).status_code
        status = int(status)
        self.assertEqual(first=status, second=403,
                         msg="POST requests without proper auth header should have 403 error but has {}".format(status))

        status = requests.post("http://localhost:8088/services/collector/event",
                               headers={"authorization": "Splunk {}".format(GLOBAL_TEST_TOKEN)}).status_code
        status = int(status)
        self.assertEqual(first=status, second=400,
                         msg="POST requests without data should have 400 error but has {}".format(status))

        status = requests.post("http://localhost:8088/services/collector/event",
                               headers={"authorization": "Splunk {}".format(GLOBAL_TEST_TOKEN)},
                               data="simple_not_json_data").status_code
        status = int(status)
        self.assertEqual(first=status, second=400,
                         msg="POST requests without json data should have 400 error but has {}".format(status))

        json_data = json.dumps({"test_without_event_field": "test"})
        status = requests.post("http://localhost:8088/services/collector/event",
                               headers={"authorization": "Splunk {}".format(GLOBAL_TEST_TOKEN)},
                               data=json_data).status_code
        status = int(status)
        self.assertEqual(first=status, second=400,
                         msg="POST requests without event key in json data should have 400 error but has {}".format(
                             status))

        json_data = json.dumps({"event": "test"})
        status = requests.post("http://localhost:8088/services/collector/event",
                               headers={"authorization": "Splunk {}".format(GLOBAL_TEST_TOKEN)},
                               data=json_data).status_code
        status = int(status)
        self.assertEqual(first=status, second=200,
                         msg="POST requests with event key,json data and proper \
                      auth header should have 200 error but has {}".format(status))

    def test_register(self):
        from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SplunkAlerterPlugin

        test_msg = "Dict should contain the SplunkPluginKey, contains {}".format(plugin_registry.keys())
        self.assertIn(member="SplunkAlerterPlugin", container=plugin_registry.keys(), msg=test_msg)

        test_msg = "Class should be SplunkAlerterPlugin, is {}".format(type(SplunkAlerterPlugin))
        self.assertIs(expr1=plugin_registry.get("SplunkAlerterPlugin"), expr2=SplunkAlerterPlugin, msg=test_msg)

        from security_monkey.alerters.custom_alerter import alerter_registry
        from security_monkey.plugins.splunk_alerter.splunk_alerter import SplunkHECAlerter

        test_msg = "Dict should contain the SplunkHECAlerter, contains {}".format(alerter_registry.keys())
        self.assertIn(member="SplunkHECAlerter", container=alerter_registry.keys(), msg=test_msg)

        test_msg = "Class should be SplunkHECAlerter, is {}".format(type(SplunkAlerterPlugin))
        self.assertIs(expr1=alerter_registry.get("SplunkHECAlerter"), expr2=SplunkHECAlerter, msg=test_msg)

    def test_create_alerter(self):
        self.assertEqual(first=self.plugin.alerters, second={},
                         msg="Alerters list should be empty at begining, is {}".format(self.plugin.alerters))
        alerter = self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)
        self.assertEqual(first=len(self.plugin.alerters), second=1,
                         msg="After creation alerters list should be 1, is {}".format(len(self.plugin.alerters)))
        dest_obj = self.plugin.get_alerter(alerter.id)
        from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SPLUNK_ALERTER_FIELDS
        for key in SPLUNK_ALERTER_FIELDS.keys():
            key_orig = getattr(alerter, key)
            key_dest = getattr(dest_obj, key)
            self.assertEqual(first=key_orig, second=key_dest,
                             msg="Field {} should be equal, orig={}, dest={}".format(key, key_orig, key_dest))
        # Cleanup list
        self.plugin.alerters = {}
        test_msg = "After deletion alerters list should be 0, is {}".format(len(self.plugin.alerters))
        self.assertEqual(first=len(self.plugin.alerters), second=0, msg=test_msg)

    def test_id_generation(self):
        token = str(uuid.uuid4())
        alerter = self.plugin.create("localhost", 8088, token, True, True)
        alerter_static_id = self.plugin.get_id_from_value("localhost", 8088, token)

        test_msg = "Alerter id should be identical, 1st={} 2nd={}".format(alerter.id, alerter_static_id)
        self.assertEqual(first=alerter.id, second=alerter_static_id, msg=test_msg)

    def test_edit_alerter_active(self):
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        alerter_before = self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)

        # Edit Active / LogConfig
        alerter_after = self.plugin.edit(alerter_id=alerter_before.id,
                                         host="localhost",
                                         port=8088,
                                         token=alerter_before.token,
                                         active=False,
                                         log_config=True)

        test_msg = "Alerters object should be different, 1st={}, 2nd={}".format(alerter_before, alerter_after)
        self.assertIsNot(expr1=alerter_before, expr2=alerter_after, msg=test_msg)

        test_msg = "Id Should be equal {} != {}".format(alerter_before.id, alerter_after.id)
        self.assertEqual(first=alerter_after.id, second=alerter_before.id, msg=test_msg)

        test_msg = "Host Should be equal {} != {}".format(alerter_before.host, alerter_after.host)
        self.assertEqual(first=alerter_after.host, second=alerter_before.host, msg=test_msg)

        test_msg = "token Should be equal {} != {}".format(alerter_before.token, alerter_after.token)
        self.assertEqual(first=alerter_after.token, second=alerter_before.token, msg=test_msg)

        test_msg = "port Should be equal {} != {}".format(alerter_before.port, alerter_after.port)
        self.assertEqual(first=alerter_after.port, second=alerter_before.port, msg=test_msg)

        test_msg = "active Should be distinct {} == {}".format(alerter_before.active, alerter_after.active)
        self.assertNotEqual(first=alerter_after.active, second=alerter_before.active, msg=test_msg)

        test_msg = "log_config Should be equal {} != {}".format(alerter_before.log_config, alerter_after.log_config)
        self.assertEqual(first=alerter_after.log_config, second=alerter_before.log_config, msg=test_msg)

        test_msg = "sourcetype Should be equal {} != {}".format(alerter_before.sourcetype, alerter_after.sourcetype)
        self.assertEqual(first=alerter_after.sourcetype, second=alerter_before.sourcetype, msg=test_msg)

        test_msg = "source Should be equal {} != {}".format(alerter_before.source, alerter_after.source)
        self.assertEqual(first=alerter_after.source, second=alerter_before.source, msg=test_msg)

        # Cleanup list
        self.plugin.alerters = {}
        test_msg = "After deletion alerters list should be 0, is {}".format(len(self.plugin.alerters))
        self.assertEqual(first=len(self.plugin.alerters), second=0, msg=test_msg)

    def test_edit_alerter_log_config(self):
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)

        alerter_before = self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)
        alerter_after = self.plugin.edit(alerter_id=alerter_before.id,
                                         host="localhost",
                                         port=8088,
                                         token=alerter_before.token,
                                         active=True,
                                         log_config=False)

        test_msg = "Alerters object should be different, 1st={}, 2nd={}".format(alerter_before, alerter_after)
        self.assertIsNot(expr1=alerter_before, expr2=alerter_after, msg=test_msg)
        test_msg = "Id Should be equal {} != {}".format(alerter_before.id, alerter_after.id)
        self.assertEqual(first=alerter_after.id, second=alerter_before.id, msg=test_msg)

        test_msg = "Host Should be equal {} != {}".format(alerter_before.host, alerter_after.host)
        self.assertEqual(first=alerter_after.host, second=alerter_before.host, msg=test_msg)

        test_msg = "token Should be equal {} != {}".format(alerter_before.token, alerter_after.token)
        self.assertEqual(first=alerter_after.token, second=alerter_before.token, msg=test_msg)

        test_msg = "port Should be equal {} != {}".format(alerter_before.port, alerter_after.port)
        self.assertEqual(first=alerter_after.port, second=alerter_before.port, msg=test_msg)

        test_msg = "active Should be equal {} != {}".format(alerter_before.active, alerter_after.active)
        self.assertEqual(first=alerter_after.active, second=alerter_before.active, msg=test_msg)

        test_msg = "log_config Should be distinct {} == {}".format(alerter_before.log_config, alerter_after.log_config)
        self.assertNotEqual(first=alerter_after.log_config, second=alerter_before.log_config, msg=test_msg)

        test_msg = "sourcetype Should be equal {} != {}".format(alerter_before.sourcetype, alerter_after.sourcetype)
        self.assertEqual(first=alerter_after.sourcetype, second=alerter_before.sourcetype, msg=test_msg)

        test_msg = "source Should be equal {} != {}".format(alerter_before.source, alerter_after.source)
        self.assertEqual(first=alerter_after.source, second=alerter_before.source, msg=test_msg)

        # Cleanup list
        self.plugin.alerters = {}
        test_msg = "After deletion alerters list should be 0, is {}".format(len(self.plugin.alerters))
        self.assertEqual(first=len(self.plugin.alerters), second=0, msg=test_msg)

    def test_edit_alerter_sourcetype(self):
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)

        alerter_before = self.plugin.create(host="localhost",
                                            port=8088,
                                            token=str(uuid.uuid4()),
                                            active=True,
                                            log_config=True,
                                            sourcetype="secmonkey")
        alerter_after = self.plugin.edit(alerter_id=alerter_before.id,
                                         host="localhost",
                                         port=8088,
                                         token=alerter_before.token,
                                         active=True,
                                         log_config=True,
                                         sourcetype="secmonkey2")

        test_msg = "Alerters object should be different, 1st={}, 2nd={}".format(alerter_before, alerter_after)
        self.assertIsNot(expr1=alerter_before, expr2=alerter_after, msg=test_msg)
        test_msg = "Id Should be equal {} != {}".format(alerter_before.id, alerter_after.id)
        self.assertEqual(first=alerter_after.id, second=alerter_before.id, msg=test_msg)

        test_msg = "Host Should be equal {} != {}".format(alerter_before.host, alerter_after.host)
        self.assertEqual(first=alerter_after.host, second=alerter_before.host, msg=test_msg)

        test_msg = "token Should be equal {} != {}".format(alerter_before.token, alerter_after.token)
        self.assertEqual(first=alerter_after.token, second=alerter_before.token, msg=test_msg)

        test_msg = "port Should be equal {} != {}".format(alerter_before.port, alerter_after.port)
        self.assertEqual(first=alerter_after.port, second=alerter_before.port, msg=test_msg)

        test_msg = "active Should be equal {} != {}".format(alerter_before.active, alerter_after.active)
        self.assertEqual(first=alerter_after.active, second=alerter_before.active, msg=test_msg)

        test_msg = "log_config Should be equal {} != {}".format(alerter_before.log_config, alerter_after.log_config)
        self.assertEqual(first=alerter_after.log_config, second=alerter_before.log_config, msg=test_msg)

        test_msg = "sourcetype Should be distinct {} != {}".format(alerter_before.sourcetype, alerter_after.sourcetype)
        self.assertNotEqual(first=alerter_after.sourcetype, second=alerter_before.sourcetype, msg=test_msg)

        test_msg = "source Should be equal {} != {}".format(alerter_before.source, alerter_after.source)
        self.assertEqual(first=alerter_after.source, second=alerter_before.source, msg=test_msg)

        # Cleanup list
        self.plugin.alerters = {}
        test_msg = "After deletion alerters list should be 0, is {}".format(len(self.plugin.alerters))
        self.assertEqual(first=len(self.plugin.alerters), second=0, msg=test_msg)

    def test_edit_alerter_source(self):
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)

        alerter_before = self.plugin.create(host="localhost",
                                            port=8088,
                                            token=str(uuid.uuid4()),
                                            active=True,
                                            log_config=True,
                                            source="secmonkey")
        alerter_after = self.plugin.edit(alerter_id=alerter_before.id,
                                         host="localhost",
                                         port=8088,
                                         token=alerter_before.token,
                                         active=True,
                                         log_config=True,
                                         source="secmonkey2")

        test_msg = "Alerters object should be different, 1st={}, 2nd={}".format(alerter_before, alerter_after)
        self.assertIsNot(expr1=alerter_before, expr2=alerter_after, msg=test_msg)
        test_msg = "Id Should be equal {} != {}".format(alerter_before.id, alerter_after.id)
        self.assertEqual(first=alerter_after.id, second=alerter_before.id, msg=test_msg)

        test_msg = "Host Should be equal {} != {}".format(alerter_before.host, alerter_after.host)
        self.assertEqual(first=alerter_after.host, second=alerter_before.host, msg=test_msg)

        test_msg = "token Should be equal {} != {}".format(alerter_before.token, alerter_after.token)
        self.assertEqual(first=alerter_after.token, second=alerter_before.token, msg=test_msg)

        test_msg = "port Should be equal {} != {}".format(alerter_before.port, alerter_after.port)
        self.assertEqual(first=alerter_after.port, second=alerter_before.port, msg=test_msg)

        test_msg = "active Should be equal {} != {}".format(alerter_before.active, alerter_after.active)
        self.assertEqual(first=alerter_after.active, second=alerter_before.active, msg=test_msg)

        test_msg = "log_config Should be equal {} != {}".format(alerter_before.log_config, alerter_after.log_config)
        self.assertEqual(first=alerter_after.log_config, second=alerter_before.log_config, msg=test_msg)

        test_msg = "sourcetype Should be equal {} != {}".format(alerter_before.sourcetype, alerter_after.sourcetype)
        self.assertEqual(first=alerter_after.sourcetype, second=alerter_before.sourcetype, msg=test_msg)

        test_msg = "source Should be distinct {} == {}".format(alerter_before.source, alerter_after.source)
        self.assertNotEqual(first=alerter_after.source, second=alerter_before.source, msg=test_msg)

        # Cleanup list
        self.plugin.alerters = {}
        test_msg = "After deletion alerters list should be 0, is {}".format(len(self.plugin.alerters))
        self.assertEqual(first=len(self.plugin.alerters), second=0, msg=test_msg)

    def test_edit_alerter_host(self):
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)

        alerter_before = self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)
        alerter_after = self.plugin.edit(alerter_id=alerter_before.id,
                                         host="127.0.0.1",
                                         port=8088,
                                         token=alerter_before.token,
                                         active=True,
                                         log_config=True)

        test_msg = "Alerters object should be different, 1st={}, 2nd={}".format(alerter_before, alerter_after)
        self.assertIsNot(expr1=alerter_before, expr2=alerter_after, msg=test_msg)
        test_msg = "Id Should be distinct {} == {}".format(alerter_before.id, alerter_after.id)
        self.assertNotEqual(first=alerter_after.id, second=alerter_before.id, msg=test_msg)

        test_msg = "Host Should be distinct {} != {}".format(alerter_before.host, alerter_after.host)
        self.assertNotEqual(first=alerter_after.host, second=alerter_before.host, msg=test_msg)

        test_msg = "token Should be equal {} != {}".format(alerter_before.token, alerter_after.token)
        self.assertEqual(first=alerter_after.token, second=alerter_before.token, msg=test_msg)

        test_msg = "port Should be distinct {} == {}".format(alerter_before.port, alerter_after.port)
        self.assertEqual(first=alerter_after.port, second=alerter_before.port, msg=test_msg)

        test_msg = "active Should be equal {} != {}".format(alerter_before.active, alerter_after.active)
        self.assertEqual(first=alerter_after.active, second=alerter_before.active, msg=test_msg)

        test_msg = "log_config Should be equal {} != {}".format(alerter_before.log_config, alerter_after.log_config)
        self.assertEqual(first=alerter_after.log_config, second=alerter_before.log_config, msg=test_msg)

        test_msg = "sourcetype Should be equal {} != {}".format(alerter_before.sourcetype, alerter_after.sourcetype)
        self.assertEqual(first=alerter_after.sourcetype, second=alerter_before.sourcetype, msg=test_msg)

        test_msg = "source Should be equal {} != {}".format(alerter_before.source, alerter_after.source)
        self.assertEqual(first=alerter_after.source, second=alerter_before.source, msg=test_msg)

        # Cleanup list
        self.plugin.alerters = {}
        test_msg = "After deletion alerters list should be 0, is {}".format(len(self.plugin.alerters))
        self.assertEqual(first=len(self.plugin.alerters), second=0, msg=test_msg)

    def test_edit_alerter_port(self):
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        alerter_before = self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)
        alerter_after = self.plugin.edit(alerter_id=alerter_before.id,
                                         host="localhost",
                                         port=8089,
                                         token=alerter_before.token,
                                         active=True,
                                         log_config=True)
        test_msg = "Alerters object should be different, 1st={}, 2nd={}".format(alerter_before, alerter_after)
        self.assertIsNot(expr1=alerter_before, expr2=alerter_after, msg=test_msg)

        test_msg = "Id Should be distinct {} == {}".format(alerter_before.id, alerter_after.id)
        self.assertNotEqual(first=alerter_after.id, second=alerter_before.id, msg=test_msg)

        test_msg = "Host Should be equal {} != {}".format(alerter_before.host, alerter_after.host)
        self.assertEqual(first=alerter_after.host, second=alerter_before.host, msg=test_msg)

        test_msg = "token Should be equal {} != {}".format(alerter_before.token, alerter_after.token)
        self.assertEqual(first=alerter_after.token, second=alerter_before.token, msg=test_msg)

        test_msg = "port Should be distinct {} == {}".format(alerter_before.port, alerter_after.port)
        self.assertNotEqual(first=alerter_after.port, second=alerter_before.port, msg=test_msg)

        test_msg = "active Should be equal {} != {}".format(alerter_before.active, alerter_after.active)
        self.assertEqual(first=alerter_after.active, second=alerter_before.active, msg=test_msg)

        test_msg = "log_config Should be equal {} != {}".format(alerter_before.log_config, alerter_after.log_config)
        self.assertEqual(first=alerter_after.log_config, second=alerter_before.log_config, msg=test_msg)

        test_msg = "sourcetype Should be equal {} != {}".format(alerter_before.sourcetype, alerter_after.sourcetype)
        self.assertEqual(first=alerter_after.sourcetype, second=alerter_before.sourcetype, msg=test_msg)

        test_msg = "source Should be equal {} != {}".format(alerter_before.source, alerter_after.source)
        self.assertEqual(first=alerter_after.source, second=alerter_before.source, msg=test_msg)

        # Cleanup list
        self.plugin.alerters = {}
        test_msg = "After deletion alerters list should be 0, is {}".format(len(self.plugin.alerters))
        self.assertEqual(first=len(self.plugin.alerters), second=0, msg=test_msg)

    def test_edit_alerter_token(self):
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        alerter_before = self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)
        alerter_after = self.plugin.edit(alerter_id=alerter_before.id,
                                         host="localhost",
                                         port=8088,
                                         token=str(uuid.uuid4()),
                                         active=True,
                                         log_config=True)

        test_msg = "Alerters object should be different, 1st={}, 2nd={}".format(alerter_before, alerter_after)
        self.assertIsNot(expr1=alerter_before, expr2=alerter_after, msg=test_msg)

        test_msg = "Id Should be distinct {} == {}".format(alerter_before.id, alerter_after.id)
        self.assertNotEqual(first=alerter_after.id, second=alerter_before.id, msg=test_msg)

        test_msg = "Host Should be equal {} != {}".format(alerter_before.host, alerter_after.host)
        self.assertEqual(first=alerter_after.host, second=alerter_before.host, msg=test_msg)

        test_msg = "token Should be distinct {} == {}".format(alerter_before.token, alerter_after.token)
        self.assertNotEqual(first=alerter_after.token, second=alerter_before.token, msg=test_msg)

        test_msg = "port Should be equal {} != {}".format(alerter_before.port, alerter_after.port)
        self.assertEqual(first=alerter_after.port, second=alerter_before.port, msg=test_msg)

        test_msg = "active Should be equal {} != {}".format(alerter_before.active, alerter_after.active)
        self.assertEqual(first=alerter_after.active, second=alerter_before.active, msg=test_msg)

        test_msg = "log_config Should be equal {} != {}".format(alerter_before.log_config, alerter_after.log_config)
        self.assertEqual(first=alerter_after.log_config, second=alerter_before.log_config, msg=test_msg)

        test_msg = "sourcetype Should be equal {} != {}".format(alerter_before.sourcetype, alerter_after.sourcetype)
        self.assertEqual(first=alerter_after.sourcetype, second=alerter_before.sourcetype, msg=test_msg)

        test_msg = "source Should be equal {} != {}".format(alerter_before.source, alerter_after.source)
        self.assertEqual(first=alerter_after.source, second=alerter_before.source, msg=test_msg)

        # Cleanup list
        self.plugin.alerters = {}
        test_msg = "After deletion alerters list should be 0, is {}".format(len(self.plugin.alerters))
        self.assertEqual(first=len(self.plugin.alerters), second=0, msg=test_msg)

    def test_delete_alerter(self):
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        alerter_before = self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)

        alerter_after = self.plugin.delete_alerter(alerter_before.id)
        test_msg = "Deleted alerter should be the same as added, 1st={}, 2nd={}".format(alerter_before, alerter_after)
        self.assertIs(expr1=alerter_before, expr2=alerter_after, msg=test_msg)

        test_msg = "Alerter list should be 0, len={}".format(len(self.plugin.alerters))
        self.assertEqual(first=0, second=len(self.plugin.alerters), msg=test_msg)

    def test_specific_watch_send_event(self):
        class ItemTest(dict):
            def __getattr__(self, item):
                return self.get(item)

            def __setattr__(self, key, value):
                self[key]=value

        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        account = Account(identifier="012345678910", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                          third_party=False, active=True)

        db.session.add(account)
        db.session.commit()

        item = ItemTest()
        item.action = "created"
        item.arn = "test_arn"
        item.index = "test_index"
        item.account = "test_acount"
        item.region = "test_region"
        item.new_config = "test_config"
        item.db_item = ItemTest()
        item.db_item.id = 1



        class NoError(Exception):
            pass

        with self.assertRaises(NoError):
            watcher = Route53(accounts=[account.name])
            watcher.created_items = [item, item, item]
            watcher.deleted_items = [item, item, item, item]
            watcher.changed_items = [item, item]

            from security_monkey.alerters.custom_alerter import alerter_registry
            splk_hec = alerter_registry.get("SplunkHECAlerter")()
            reports_events = splk_hec.report_watcher_changes(watcher)
            eprint(reports_events)
            test_msg = "Count of reported items should be 9 and is {}".format(len(reports_events))
            self.assertEqual(first=len(reports_events), second=9, msg=test_msg)
            raise NoError()

        db.session.remove()

    def test_specific_auditor_send_event(self):
        class ItemTest(dict):
            def __getattr__(self, item):
                return self.get(item)

            def __setattr__(self, key, value):
                self[key] = value

        account_type_result = AccountType(name='AWS')
        db.session.add(account_type_result)
        db.session.commit()

        account = Account(identifier="012345678910", name="TEST_ACCOUNT",
                          account_type_id=account_type_result.id, notes="TEST_ACCOUNT",
                          third_party=False, active=True)

        db.session.add(account)
        db.session.commit()

        issue = ItemTest()
        issue.id = "issue_id"
        issue.arn = "test_arn"
        issue.index = "test_index"
        issue.account = "test_acount"
        issue.region = "test_region"
        issue.issue = "test_issue"
        issue.notes = "test_notes"

        class NoError(Exception):
            pass

        with self.assertRaises(NoError):
            auditor = ELBAuditor(accounts=[account.name])

            auditor.items = [ItemTest()]
            auditor.items[0].confirmed_new_issues = [issue, issue]
            auditor.items[0].confirmed_fixed_issues = [issue, issue, issue]
            auditor.items[0].db_item = ItemTest()
            auditor.items[0].db_item.id = 1
            eprint(auditor.items)

            from security_monkey.alerters.custom_alerter import alerter_registry
            splk_hec = alerter_registry.get("SplunkHECAlerter")()

            reports_events = splk_hec.report_auditor_changes(auditor)
            test_msg = "Count of reported items should be 5 and is {}".format(len(reports_events))
            self.assertEqual(first=len(reports_events), second=5, msg=test_msg)
            raise NoError()

        db.session.remove()

    def test_bad_receiver_host(self):
        from security_monkey.plugins.splunk_alerter.splunk_alerter_exceptions import SplunkAlerterFieldFormatError
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        with self.assertRaises(SplunkAlerterFieldFormatError):
            self.plugin.create("loc alhost", 8088, str(uuid.uuid4()), True, True)

    def test_bad_receiver_port(self):
        from security_monkey.plugins.splunk_alerter.splunk_alerter_exceptions import SplunkAlerterFieldFormatError
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        with self.assertRaises(SplunkAlerterFieldFormatError):
            self.plugin.create("localhost", -8088, str(uuid.uuid4()), True, True)

    def test_bad_receiver_token(self):
        from security_monkey.plugins.splunk_alerter.splunk_alerter_exceptions import SplunkAlerterFieldFormatError
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        with self.assertRaises(SplunkAlerterFieldFormatError):
            self.plugin.create("localhost", 8088, str(uuid.uuid4())+"badtoken", True, True)

    def test_duplicate_added(self):
        from security_monkey.plugins.splunk_alerter.splunk_alerter_exceptions import SplunkAlerterExists
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        with self.assertRaises(SplunkAlerterExists):
            self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)
            self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)

    def test_get_not_found(self):
        from security_monkey.plugins.splunk_alerter.splunk_alerter_exceptions import SplunkAlerterNotFound
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        with self.assertRaises(SplunkAlerterNotFound):
            self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)
            self.plugin.get_alerter(self.plugin.get_id_from_value("localhost", 8089, str(uuid.uuid4())))

    def test_edit_not_found(self):
        from security_monkey.plugins.splunk_alerter.splunk_alerter_exceptions import SplunkAlerterNotFound
        test_msg = "Alerters list should be empty at begining, is {}".format(self.plugin.alerters)
        self.assertEqual(first=self.plugin.alerters, second={}, msg=test_msg)
        with self.assertRaises(SplunkAlerterNotFound):
            self.plugin.create("localhost", 8088, str(uuid.uuid4()), True, True)
            self.plugin.edit("notandid", "localhost", 8088, str(uuid.uuid4()), True, True)
