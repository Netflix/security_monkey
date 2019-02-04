JIRA Synchronization
====================

Overview
--------

JIRA synchronization is a feature that allows Security Monkey to automatically create and update JIRA tickets based on issues it finds. Each ticket corresponds to a single type of issue for a single account. The tickets contain the number of open issues and a link back to the Security Monkey details page for that issue type.

Configuring JIRA Synchronization
--------------------------------

To use JIRA sync, you will need to create a YAML configuration file, specifying several settings.

~~~~ {.sourceCode .yaml
 server: https://jira.example.com
 account: securitymonkey-service
 password: hunter2
 project: SECURITYMONKEY
 issue_type: Task
 url: https://securitymonkey.example.com
 ip_proxy: example.proxy.com
 port_proxy: 443
 assignee: SecMonkeyJIRA
 only_update_on_change: false
}
~~~~

`server` - The location of the JIRA server. `account` - The account with which Security Monkey will create tickets `password` - The password to the account. `project` - The project key where tickets will be created. `issue_type` - The type of issue each ticket will be created as. `url` - The URL for Security Monkey. This will be used to create links back to Security Monkey. `disable_transitions` - If true, Security Monkey will not close or reopen tickets. This is false by default. `ip_proxy` - Optional proxy endpoint for JIRA client. NOTE: Proxy authentication not currently supported. `port_proxy` - Optional proxy port for JIRA client. NOTE: Proxy authentication not currently supported. `assignee` - Optional default assignee for generated JIRA tickets. Assignee should be username. `only_update_on_change` - Optional (defaults to false), if true tickets only update if the count has changed.

### Using JIRA Synchronization

To use JIRA sync, set the environment variable `SECURITY_MONKEY_JIRA_SYNC` to the location of the YAML configuration file. This file will be loaded once when the application starts. If set, JIRA sync will run for each account after the auditors run. You can also manually run a sync through `manage.py`.

`monkey sync_jira`

Details
-------

Tickets are created with the summary:

`<Issue text> - <Technology> - <Account name>`

And the description:

`` ` This ticket was automatically created by Security Monkey. DO NOT EDIT ANYTHING BELOW THIS LINE Number of issues: X Account: Y View on Security Monkey Last Updated: TIMESTAMP ``\`

Security Monkey will update tickets based on the summary. If it is changed in any way, Security Monkey will open a new ticket instead of updating the existing one. When updating, the number of issues and last updated fields will change. Security Monkey will preserve all text in the description before "This ticket was automatically created by Security Monkey", and remove anything after.

Security Monkey will automatically close tickets when they have zero open issues, by setting the state of the ticket to "Closed". Likewise, it will reopen a closed ticket if there are new open issues. This feature can be disabled by setting `disable_transitions: true` in the config.

Justifying an issue will cause it to no longer be counted as an open issue.

If an auditor is disabled, its issues will no longer be updated, opened or closed.

Logs
----

JIRA sync will generate the following log lines.

`Created issue <summary>` (debug) - A new JIRA ticket was opened.

`Updated issue <summary>` (debug) - An existing ticket was updated.

`Error creating ticket: <error>` (error) - An error was encounted when creating a ticket. This could be due to a misconfigured project name, issue type or connectivity problems.

`JIRA sync configuration missing required field: <error>` (error) - One of the 6 required fields in the YAML configuration is missing.

`Error opening JIRA sync configuration file: <error>` (error) - Security Monkey could not open the file located at `SECURITY_MONKEY_JIRA_SYNC`.

`JIRA sync configuration file contains malformed YAML: <error>` (error) - The YAML could not be parsed.

`Syncing issues with Jira` (info) - Auditors have finished running and JIRA sync is starting.

`Error opening/closing ticket: <error>`: (error) - Security Monkey tried to set an issue to "Closed" or "Open". This error may mean that these transitions are named differently in your JIRA project. To disable ticket transitions, set `disable_transitions: true` in the config file.
