*********
Changelog
*********


v0.3.8 (2015-08-28)
===================
- PR #165 - echiu64 - S3 watcher now tracking S3 Logging Configuration.
- None - monkeysecurity - Certs with an invalid issuer now flagged.
- PR #177 - DenverJ -Added new SQS Auditor.
- PR #188 - kevgliss - Removed dependency on M2Crypto/Swig and replaced with Cryptography.
- PR #164 - Qmando - URL encoding issue with certain searches containing spaces corrected.
- None - monkeysecurity - Fixed issue where corrected issues were not removed.
- PR #198 - monkeysecurity - Adding ability to select up to four items or revisions to be compared.
- PR #194 #195 - bunjiboys - SECURITY_TEAM_EMAIL should accept not only a list, but also a string or tuple.
- PR #180 #181 #190 #191 #192 #193 - cbarrac - A number of udpates and fixes for the bash installer. (scripts/secmonkey_auto_installer.sh)
- PR #176 #178 - mikegrima - Updated documentation for contributors on OS X and Ubuntu to use Webstorm instead of the Dart Editor.


Contributors:

- Qmando
- echiu64
- DenverJ
- cbarrac
- kevgliss
- mikegrima
- monkeysecurity


v0.3.7 (2015-07-20)
===================
- PR #122 - Qmando - Jira Sync.  Quentin from Yelp added Jira Integration.
- PR #147 - echiu64 - Added colors to audit emails and added missing justifications back into emails.
- PR #150 - echiu64 - Fixed a missing comma from setup.py
- PR #155 - echiu64 - Fixed a previous merge issue where _audit_changes() was looking for a Monitor instance instead of an list of Auditors.
- Issue #154 - monkeysecurity - Added support for ELB Reference Policy 2015-05.
- None - monkeysecurity - Added db.session.refresh(...) where appropriate in a few API views to replace some very ugly code.
- Issue #133 - lucab - Upgraded Flask-RESTful from v0.2.5 to v0.3.3 to fix an issue where request arguments were being persisted as the string "None" when they should have remained the javascript literal null.
- PR #120 - lucab - Add custom role_name field for each account to replace the previously hardcoded 'SecurityMonkey' role name.
- PR #120 - gene1wood - Add support for the custom role_name into manage.py.
- PR #161 - Asbjorn Kjaer - Increase s3_name from 32 characters to 64 characters to avoid errors or truncation where s3_name is longer.
- None - monkeysecurity - Set the 'defer' (lazy-load) attribute for the JSON config column on the ItemRevision table.  This speeds up the web API in a number of places.


Hotfixes:

- Issue #149 - Python scoping issue where managed policies attached to more than one entity would cause an error.
- Issue #152 - SNS topics were being saved by ARN instead of by name, causing exceptions for very long names.
- Issue #141 - Setup cascading deletes on the Account table to prevent the error which occured when trying to delete an account with items and users attached.


Contributors:

- Qmando
- echiu64
- lucab
- gene1wood
- Asbjorn Kjaer (akjaer)
- monkeysecurity


v0.3.6 (2015-04-09)
===================
- Changes to issue score in code will now cause all existing issues to be re-scored in the database.
- A new configuration parameter called SECURITYGROUP_INSTANCE_DETAIL can now be set to:
    - "FULL": Security Groups will display each instances, and all instance tags, that are associated with the security group.
    - "SUMMARY": Security Groups will display the number of instances attached to the security group.
    - "NONE": Security Groups will not retrieve any data about instances attached to a security group.
    - If SECURITY_GROUP_INSTANCE_DETAIL is set to "FULL" or "SUMMARY", empty security groups audit issues will have their score set to zero.
    - For accounts with many thousands of instances, it is advised to set this to "NONE" as the AWS API's do not respond in a timely manner with that many instances.
- Each watcher can be set to run at a different interval in code.  We will want to move this to be a UI setting.
- Watchers may specify a list of ephemeral paths.  Security_monkey will not send out change alerts for items in the ephemeral section.  This is a good place for metadata that is often changing like the number of instances attached to a security_group or the number of remaining IP addresses in a VPC subnet.

Contributors:

- lucab
- monkeysecurity

v0.3.5 (2015-03-28)
===================
- Adding policy minimizer & expander to the revision component
- Adding tracking of instance profiles attached to a role
- Adding marker/pagination code to redshift.describe_clusters()
- Adding pagination to IAM User get_all_user_policies, get_all_access_keys, get_all_mfa_devices, get_all_signing_certs
- Typo & minor corrections on postgres commands
- CLI command to save your current configurations to a JSON file for backup
- added a VPC watcher
- Adding DHCP Options and Internet Gateways to the VPC Watcher
- Adding a subnet watcher. Fixing the VPC watcher with deep_dict
- Adding the vpc route_table watcher
- Removing subnet remaining IP field until ephemeral section is merged in
- Adding IAM Managed Policies
- Typo & minor corrections on postgres commands in documentation
- Adds ELBSecurityPolicy-2015-03. Moves export grade ciphers to their own section and alerts on FREAK vuln.
- Provides context on refpol 2015-03 vs 2015-02.
- Adding a Managed Policies Auditor
- Added Manged Policy tracking to the IAM users, groups, and roles


Summary of new watchers:

- vpc
    - DHCP Options
    - Internet Gateways
- subnet
- routetable
- managed policies


Summary of new Auditors or audit checks:

- managed policies
- New reference policy 2015-03 for ELB listeners.
- New alerts for FREAK vulnerable ciphers.


Contributors:

- markofu
- monkeysecurity

v0.3.4 (2015-2-19)
==================
- Merged in a new AuditorSettings tab created by Qmando at Yelp enabling you to disable audit checks with per-account granularity.
- security_monkey is now CSP compliant.
- security_monkey has removed all shadow-DOM components.  Also removed webcomponents.js and dart_support.js, as they were not CSP compliant.
- security_monkey now advises users to enable standard security headers following headers:

.. code-block:: python

    X-Content-Type-Options "nosniff";
    X-XSS-Protection "1; mode=block";
    X-Frame-Options "SAMEORIGIN";
    Strict-Transport-Security "max-age=631138519";
    Content-Security-Policy "default-src 'self'; font-src 'self' https://fonts.gstatic.com; script-src 'self' https://ajax.googleapis.com; style-src 'self' https://fonts.googleapis.com;"


- security_monkey now has XSRF protection against all DELETE, POST, PUT, and PATCH calls.
- Updated the ELB Auditor to be aware of the ELBSecurityPolicy-2015-02 reference policy.


Contributers:

- Qmando
- monkeysecurity


v0.3.3 (2015-2-3)
=================
- Added MirorsUsed() to my dart code to reduce compiled javascript size.
- Added support for non-chrome browsers by importing webcomponents.js and dart_support.js
- Upgraded to Angulardart 1.1.0 and Angular-dart.ui 0.6.3

v0.3.2 (2015-1-20)
==================
- A bug has been corrected where IAM Groups with > 100 members or policies would be truncated.
- The web UI has been updated to use AngularDart 1.0.0.  Significantly smaller javascript size.

v0.3.1 (2015-1-11)
==================
- Change emails again show issues and justifications.
- Change emails now use jinja templating.
- Fixed an issue where issue justifications would disappear when the item was changed.
- Merged a pull request from github user jijojv to start the scheduler at launch instead of waiting 15 minutes.

v0.3.0 (2014-12-19)
===================
- Add localhost to CORS for development.
- Big refactor adding monitors.  Adding new watchers/auditors is now much simpler.
- Return to the current URL after authenticating.
- Added SES_REGION config.  Now you can send email out of regions other than us-east-1.
- Changing default log location to /var/log/security_monkey.
- Docs now have cleaner nginx.conf.
- Add M2Crypto to get a number of new iamssl fields.
- Added favicon.

new watchers:

- eip
- redshift
- ses

enhanced watchers:

- iamssl - new fields from m2crypto
- elb - new listener policies from botocore
- sns - added sns subscriptions
- s3 - now tracks lifecycle rules

new auditors:

- redshift - checks for non-vpc deployment.
- ses - checks for verified identities

enhanced auditors:

- iamssl - cert size, signature hashing algorithm, upcoming expiration, heartbleed
- elb - check reference policy and certain custom policy fields

hotfixes:

- Fixed issue #12 - Deleting account results in foreign key constraint.
- Added missing alembic script for the ignorelist.
- Various minor documentation updates.
- API server now respects --bind parameter. (Required for the docker image).
- SES connection in utils.py is now surrounded in a try/except.
- FlaskSecurity upgraded to latest.

Contributers:

- ivanlei
- lucab
- yograterol
- monkeysecurity

v0.2.0 (2014-10-31)
===================

Changes in the Web UI:

- Dart: Dates are now displayed in your local timezone.
- Dart: Added Item-level comments.
- Dart: Added the ability to bulk-justify issues from the Issues Table view. This uses the AngularDartUI Modal Component.
- Dart: Added better messaging around the settings for adding an account.  This closes issue #38. This uses the AngularDartUI tooltip component.
- Bug Fix: Colors in the Item table now correctly represent the justification status.
- Dart: Added AngularUI Tabs to select between diff and current configuration display.
- Dart: Added a timer-based auto-refresh so SM can be used as a dashboard.
- Dart: Replaced a number of custom http services with Victor Savkin's Hammock library.
  - More than 965 lines of code removed after using Hammock.
- Dart: Replaced custom pagination code with AngularDartUI's Pagination Component.
  - IssueTable
  - RevisionTable
  - ItemTable
  - AccountSettingsTable
- Dart: Network CIDR whitelist is now configured in the web UI under settings.
- Dart: Object Ignorelist is now configured in the web UI under settings.
- Created a new PaginatedTable parent class for all components that wish to display paginated data.  This table works with AngularDart's Pagination Component and also provides the ability to change the number of items displayed on each page.
- Dart: Added ng_infinite_scroll to the item_detail_view for loading revisions
- Dart: Moved a number of components from being their own libraries to being ```part of``` the security_monkey library.
- Dart: Replaced the last controller (UsernameController) with a Component to prepare for AngularDart 1.0.0
- Dart: Style - Renamed library from SecurityMonkey to security_monkey to follow the dart style guide.  Refactored much of main.dart into lib/security_monkey.dart to try and mimic the cleaner design of the new angular sample app: https://github.com/vsavkin/angulardart-sample-app

Changes in the core product:

- Updated API endpoints to better follow REST architecture.
- Added table for NetworkWhitelist.
- Added rest API endpoints for NetworkWhitelist.
- Added Alembic migration script to add the new NetworkWhitelist table to the DB.
- Added table for IgnoreList.
- Added rest API endpoints for Ignorelist.
- Added Alembic migration script to add the new IgnoreList table to the DB.
- Added check for rfc-1918 CIDRs in non-VPC security groups.
- Saving IAMSSL Certs by cert name instead of cert ID
- Marking VPC RDS Security Groups with their VPC ID
- Supports Paginated Boto access for RDS Security Groups.
- Added alert for non-VPC RDS SG's containing RFC-1918 CIDRs
- Added check for IAM USER AKEY rotation
- Added check for IAM USER with login profile (console access) And Access Keys (API Access)
- Added an ELB Auditor with a check for internet-facing ELB.
- Added check for security groups with large port ranges.

v0.1.2 (2014-08-11)
===================

Changes in the Web UI:

- Dart: Removed Shadow DOM dependency and set version bounds in pubspec.yaml.
- Dart: Replaced package:js with dart:js.
- Dart: Added the Angular Pub Transformer.

Changes in the core product:

- Added AWS Rate Limiting Protection with exponential backoff code.
- Added instructions to get a local development environment setup for contributing to security_monkey.
- Added support for boto's new ELB pagination.  The pull request to boto and to security_monkey came from Kevin Glisson.
- Bug fix: Security Group Audit Issues now include the port the issue was reported on.


These were already in master, but weren't tied to a new release:

- Bug fix: Supervisor script now sets SECURITY_MONKEY_SETTINGS envvar for the API server whereas it only previously set the envvar for the scheduler. This came from a pull request from parabolic.
- Bug fix: Audit reports will only be sent if there are issues to report on.
- Bug fix: Daily Audit Email setting (ALL/NONE/ISSUES) is now respected.
- Bug fix: Command Line Auditor Command Arguments are now coerced into being booleans.
- Quickstart Guide now instructs user to setup the web UI on SSL.
- Various Smaller Bug Fixes.

v0.1.1 (2014-06-30)
=====================

Initial release of Security Monkey!
