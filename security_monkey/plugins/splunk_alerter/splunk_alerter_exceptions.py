from security_monkey.exceptions import SecurityMonkeyException
from security_monkey import app


class SplunkAlerterExists(SecurityMonkeyException):
    """Security Monkey Account name exists... cannot rename or create an account with that name"""
    def __init__(self, alerter_host, alerter_port):
        self.alerter_host = alerter_host
        self.alerter_port = alerter_port
        app.logger.info(self)

    def __str__(self):
        return repr("Alerter with url: {}:{} already exists. Cannnot create"
                    " or rename account with this name.".format(self.alerter_host, self.alerter_port))

class SplunkAlerterNotFound(SecurityMonkeyException):
    """Security Monkey Account name exists... cannot rename or create an account with that name"""
    def __init__(self, alerter_id):
        self.alerter_id = alerter_id
        app.logger.info(self)

    def __str__(self):
        return repr("Alerter with id: {} does not exists".format(self.alerter_id))

class SplunkAlerterNetworkExecption(SecurityMonkeyException):
    """Security Monkey Account name exists... cannot rename or create an account with that name"""
    def __init__(self, status_code, msg):
        self.status_code = status_code
        self.msg = self.msg
        app.logger.warn(self)

    def __str__(self):
        return repr("Receiver did not receive log corretly sc={}, msg={}".format(self.status_code, self.msg))


class SplunkAlerterFieldFormatError(SecurityMonkeyException):
    """Security Monkey Account name exists... cannot rename or create an account with that name"""
    def __init__(self, field, field_value):
        self.field = field
        self.field_value = field_value
        app.logger.info(self)

    def __str__(self):
        return repr("Alerter field {} with value {} is incorrect.".format(self.field, self.field_value))
