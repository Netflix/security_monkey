
Splunk Alerter Plugin
============================

Configuration on Splunk Indexer
-------------------

You have to enable http event collector on the indexer.
Default port is ***8088***

To enable it, add an ***inputs.conf*** file to your configuration
Here an example of our configuration, don't worry  the token is a fake but match the pattern of real one

    [http]
    disabled = 0
    enableSSL = 1
    index = test
    
    [http://security_monkey]
    token = ba903130-9c5f-4164-81fd-687714b02181
    index = intern_security_monkey_lab
    sourcetype = securitymonkey:json
    disabled = 0


Configuration on Security Monkey
-------------------    
    
You can disable HTTPS but it's not recommanded since you can forward critical data in cleartext
However if you REALLY want to disbale https you have to edit `security_monkey/plugins/splunk_alerter/splunk_alerter.py`
from:

    def create_hec(self):
        if self.hecs is not None:
            return
        from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SplunkAlerterPlugin
        alerters = SplunkAlerterPlugin().get_alerters()
        self.hecs = []
        for alerter in alerters:
            hec = http_event_collector(token=alerter.token, http_event_port=alerter.port, http_event_server=alerter.host)   
          
to:

    def create_hec(self):
        if self.hecs is not None:
            return
        from security_monkey.plugins.splunk_alerter.splunk_alerter_plugin import SplunkAlerterPlugin
        alerters = SplunkAlerterPlugin().get_alerters()
        self.hecs = []
        for alerter in alerters:
            hec = http_event_collector(token=alerter.token, http_event_port=alerter.port, http_event_server=alerter.host, http_event_server_ssl=False)    
            

When all in code is done you can go to the UI to add the alerter in the config section.
It will ask you :
 * The FQDN of the indexer (or ip)
 * The port HEC is running (8088 by default)
 * The token you defined on the indexer (here ba903130-9c5f-4164-81fd-687714b02181)
 * the sourcetype prefix (optionnal by default it's "securitymonkey:auditor" and "securitymonkey:watch")
 * the source by default secdev
 
 * If you want to enable the alerter : i.e. if you want data to be send to Splunk
 * If you want a copy of the config : i.e. when a avent triggered a copy of the item configuration is send to splunk too

