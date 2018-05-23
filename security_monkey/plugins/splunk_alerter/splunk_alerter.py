from security_monkey import app
from security_monkey.plugins.splunk_alerter.http_event_collector import http_event_collector
from security_monkey.alerters.custom_alerter import AlerterType


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
        from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SplunkAlerterPlugin
        alerters = SplunkAlerterPlugin().get_alerters()
        self.hecs = []
        for alerter in alerters:
            hec = http_event_collector(token=alerter.token, http_event_port=alerter.port, http_event_server=alerter.host)
            hec.log_config = alerter.log_config
            hec.sourcetype = alerter.sourcetype
            hec.source = alerter.source
            self.hecs.append(hec)

    def handle_events(self, events, caller):
        self.create_hec()
        for hec in self.hecs:
            payload = {}
            payload.update({"sourcetype": "{}:{}".format(hec.sourcetype, caller)})
            payload.update({"source": "{}".format(hec.source)})
            payload.update({"host": app.config.get("FQDN")})
            for event in events:
                if not hec.log_config:
                    event["current_config"] = None
                payload.update({"event":event})
                app.logger.debug("Will send {}".format(event))
                hec.batchEvent(payload)
        for hec in self.hecs:
            hec.flushBatch()

    def report_watcher_changes(self, watch):
        events = []
        for item in watch.created_items:
            event = {
                "action": "created",
                "object_id": item.arn,
                "object": item.index,
                "account": item.account,
                "dest": item.region,
                "object_path": item.arn,
                "current_config": item.new_config,
                "item_url": 'https://{}:{}/#/viewitem/{}'.format(app.config.get('FQDN'), app.config.get('WEB_PORT'),item.db_item.id),
                "vendor_product":"security_monkey"
            }
            events.append(event)

        for item in watch.changed_items:
            event = {
                "action": "modified",
                "object_id": item.arn,
                "object": item.index,
                "account": item.account,
                "dest": item.region,
                "current_config" : item.new_config,
                "item_url": 'https://{}:{}/#/viewitem/{}'.format(app.config.get('FQDN'), app.config.get('WEB_PORT'),item.db_item.id),
                "vendor_product": "security_monkey"
            }
            events.append(event)

        for item in watch.deleted_items:
            event = {
                "action": "deleted",
                "object_id": item.arn,
                "object": item.index,
                "account": item.account,
                "dest": item.region,
                "item_url": 'https://{}:{}/#/viewitem/{}'.format(app.config.get('FQDN'), app.config.get('WEB_PORT'),item.db_item.id),
                "vendor_product": "security_monkey"
            }
            events.append(event)
        if len(events) > 0:
            self.handle_events(events, "watch")
        return events

    def report_auditor_changes(self, auditor):
        events = []
        for item in auditor.items:
            for issue in item.confirmed_new_issues:
                event = {
                    "action": "issue",
                    "status":"create",
                    "issue_id": issue.id,
                    "item_id": item.db_item.id,
                    "item_url": 'https://{}:{}/#/viewitem/{}'.format(app.config.get('FQDN'), app.config.get('WEB_PORT'),item.db_item.id),
                    "resource": item.index,
                    "account": item.account,
                    "region": item.region,
                    "object_id": item.arn,
                    "body": issue.issue
                }
                events.append(event)

            for issue in item.confirmed_fixed_issues:
                event = {
                    "action": "issue",
                    "status":"fix",
                    "issue_id": issue.id,
                    "item_id": item.db_item.id,
                    "item_url": 'https://{}:{}/#/viewitem/{}'.format(app.config.get('FQDN'), app.config.get('WEB_PORT'),item.db_item.id),
                    "resource": item.index,
                    "account": item.account,
                    "region": item.region,
                    "object_id": item.arn,
                    "issue": issue.issue,
                    "notes": issue.notes
                }
                events.append(event)
        if len(events) > 0:
            self.handle_events(events, "auditor")
        return events
