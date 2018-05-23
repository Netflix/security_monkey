from security_monkey.plugin import SMPlugin
from security_monkey import api, app
from flask_restful import fields
from security_monkey.plugins.splunk_alerter.splunk_alerter_exceptions import SplunkAlerterExists, SplunkAlerterNotFound, SplunkAlerterFieldFormatError


import json
import uuid
import re

SPLUNK_ALERTER_FIELDS = {
    'id': fields.String,
    'host': fields.String,
    'port': fields.Integer,
    'token': fields.String,
    'active': fields.Boolean,
    'log_config': fields.Boolean,
    'sourcetype': fields.String,
    'source': fields.String
}


class SplunkAlerterPlugin(SMPlugin):
    instance = None
    index = 'splunkalerter'

    class InternSplunkAlerter:
        def __init__(self, json_array=None):
            if json_array is None:
                self.id = uuid.uuid4()
            else:
                for key in SPLUNK_ALERTER_FIELDS.keys():
                    setattr(self, key, json_array.get(key))
                self.validate()

        def __str__(self):
            return json.dumps(self.to_dict())

        def to_dict(self):
            ret = {}
            for key in SPLUNK_ALERTER_FIELDS.keys():
                ret[key] = getattr(self, key)
            return ret

        def validate(self):
            if not isinstance(self.port, int):
                raise SplunkAlerterFieldFormatError("port", self.port)
            if self.port < 0 or self.port > 65535:
                raise SplunkAlerterFieldFormatError("port", self.port)
            dns_re = r"""^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-\_]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"""
            if not re.match(dns_re, self.host, re.MULTILINE):
                raise SplunkAlerterFieldFormatError("host", self.host)
            uuid_re = "^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$"
            if not re.match(uuid_re, self.token):
                raise SplunkAlerterFieldFormatError("token", self.token)

            if self.sourcetype is None or self.sourcetype == "":
                self.sourcetype = "securitymonkey"
            if self.source is None or  self.source == "":
                self.source = "secdev"

    def __init__(self):
        self.alerters = {}
        SMPlugin.__init__(self)


    @classmethod
    def register(cls):
        import security_monkey.plugins.splunk_alerter.splunk_alerter_view as views
        app.logger.debug("Registering SplunkAlerter views %s")
        api.add_resource(views.SplunkAlerterPostList, '/api/1/splunk_alerter')
        api.add_resource(views.SplunkAlerterGetPutDelete, '/api/1/splunk_alerter/<string:alerter_id>')

    def convert_to_json(self):
        dictionnify = {}
        for key in self.alerters.keys():
            dictionnify[key] = self.alerters.get(key).to_dict()
        return json.dumps(dictionnify)

    def build(self):
        object_json = json.loads(self.config)
        self.alerters = {}
        for key in object_json.keys():
            self.alerters[key] = SplunkAlerterPlugin.InternSplunkAlerter(object_json.get(key))

    @staticmethod
    def get_id_from_value(host, port, token):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, "{}:{}/{}".format(host, port, token)))

    def get_alerter(self, alerter_id):
        if alerter_id not in self.alerters.keys():
            raise SplunkAlerterNotFound(alerter_id)
        return self.alerters.get(alerter_id)

    def get_alerters(self):
        return self.alerters.values()

    def get_alerter_with_log_config(self, log_config=True):
        app.logger.debug(vars([tmp_alerter for tmp_alerter in self.alerters.values() if tmp_alerter.log_config == log_config]))
        return [tmp_alerter for tmp_alerter in self.alerters.values() if tmp_alerter.log_config == log_config]

    def get_active_alerter(self, active=True):
        app.logger.debug(vars([tmp_alerter for tmp_alerter in self.alerters.values() if tmp_alerter.active == active]))
        return [tmp_alerter for tmp_alerter in self.alerters.values() if tmp_alerter.active == active]

    def edit(self, alerter_id, host, port, token, active, log_config, sourcetype="securitymonkey", source="secdev"):
        build_alerter = [tmp_alerter for tmp_alerter in self.alerters.values() if tmp_alerter.id == alerter_id]
        if len(build_alerter) == 0:
            raise SplunkAlerterNotFound(alerter_id)
        if len(build_alerter) == 1 and build_alerter[0].id != alerter_id:
            raise SplunkAlerterExists(host, port)
        if len(build_alerter) > 1:
            raise SplunkAlerterExists(host, port)

        self.alerters.pop(alerter_id)
        build_alerter = SplunkAlerterPlugin.InternSplunkAlerter()
        build_alerter.id = self.get_id_from_value(host, port, token)
        build_alerter.host = host
        build_alerter.port = port
        build_alerter.token = token
        build_alerter.active = active
        build_alerter.log_config = log_config
        build_alerter.sourcetype = sourcetype
        build_alerter.source = source
        self.__set_alerter(build_alerter)
        return build_alerter

    def create(self, host, port, token, active, log_config, sourcetype="securitymonkey:", source="secdev"):
        build_alerter = [tmp_alerter for tmp_alerter in self.alerters.values()
                         if tmp_alerter.host == host and tmp_alerter.port == port]
        if len(build_alerter) >= 1:
            raise SplunkAlerterExists(host, port)
        alerter = SplunkAlerterPlugin.InternSplunkAlerter()
        alerter.id = self.get_id_from_value(host, port, token)
        alerter.host = host
        alerter.port = port
        alerter.token = token
        alerter.active = active
        alerter.log_config = log_config
        alerter.sourcetype = sourcetype
        alerter.source = source
        self.__set_alerter(alerter)
        return alerter

    def __set_alerter(self, alerter, validate=True):
        if validate:
            alerter.validate()
        self.alerters[alerter.id] = alerter
        self.save_config(self.__class__.__name__)

    def delete_alerter(self, alerter_id):
        alerter = None
        try:
            alerter = self.alerters.pop(alerter_id, None)
        except KeyError:
            pass
        self.save_config(self.__class__.__name__)
        return alerter
