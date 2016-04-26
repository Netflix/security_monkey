*********
Changelog
*********

v0.5.0 (2016-04-26)
===================
- PR #286 - bunjiboys - Added Seoul region AWS Account IDs to import scripts
- PR #291 - sbasgall - Corrected ignore_list.py variable names and help strings
- PR #284 - mikegrima - Fixed cross-account root reporting for ES service (Issue #283)
- PR #293 - mikegrima - Updated quickstart documentation to remove permission wildcards (Issue #287)
- PR #301 - monkeysecurity - iamrole watcher can now handle many more roles (1000+) and no longer times out.
- PR #316 - DenverJ - Handle database exceptions by cleaning up session.
- PR #289 - delikat - Persist custom role names on account creation
- PR #321 - monkeysecurity - Item List and Item View will no longer display disabled issues.
- PR #322 (PR #308) - llange - Ability to add AWS owned managed policies to ignore list by ARN (Issue #148)
- PR #323 - snixon - Breaks check_securitygroup_any into ingress and egress (Issue #239)
- PR #309 - DenverJ -  Significant database query optimizations by tuning itemrevision retrievals
- PR #324 - mikegrima - Handling invalid ARNs more consistently between watchers (Issue #248)
- PR #317 - ollytheninja - Add Role Based Access Control
- PR #327 - monkeysecurity - Added Flask-Security's SECURITY_TRACKABLE to backend and UI
- PR #328 - monkeysecurity - Added ability to parse AWS service "ARNs" like events.amazonaws.com as well as ARNS that use * for the account number like `arn:aws:s3:​*:*​:some-s3-bucket`
- PR #314 - pdbogen - Update Logging to have the ability to log to stdout, useful for dockerizing.

Hotfixes:

- s3_acl_compare_lowercase: AWS now returns S3 ACLs with a lowercased owner.  security_monkey now does a case insensitive compare
- longer_resource_ids. Updating DB to handle longer AWS resource IDs: https://aws.amazon.com/blogs/aws/theyre-here-longer-ec2-resource-ids-now-available/
- Removed requests from requirements.txt/setup.py as it was pinned to a very old version and not directly required (Issue #312)
- arn_condition_awssourcearn_can_be_list. Updated security_monkey to be able to handle a list of ARNS in a policy condition.
- ignore_list_fails_on_empty_string: security_monkey now properly handles an ignorelist entry containing a prefix string of length 0.
- protocol_sslv2_deprecation: AWS stopped returning whether an ELB listener supported SSLv2.  Fixed security_monkey to handle the new format correctly.

Important Notes:

- security_monkey IAM roles now require a new permission: `iam:listattachedrolepolicies`
- Your security_monkey config file should contain a new flag: `SECURITY_TRACKABLE = True`
- You'll need to rerun `python setup.py install` to obtain the new dependencies.

Contributors:

- @bunjiboys
- @sbasgall
- @mikegrima
- @DenverJ
- @delikat
- @snixon
- @ollytheninja
- @pdbogen
- @monkeysecurity


v0.4.1 (2015-12-22)
===================
- PR #269 - mikegrima - TravisCI now ensures that dart builds.
- PR #270 - monkeysecurity - Refactored sts_connect to dynamically import boto resources.
- PR #271 - OllyTheNinja-Xero - Fixed indentation mistake in auditor.py
- PR #275 - AlexCline - Added elb logging to ELB watcher and auditor.
- PR #279 - mikegrima - Added ElasticSearch Watcher and Auditor (with tests).
- PR #280 - monkeysecurity - PolicyDiff better handling of changes to primitives (like ints) in dictionay values and added explicit escaping instead of relying on Angular.
- PR #282 - mikegrima - Documentation Fixes to configuration.rst and quickstart.rst adding es: permissions and other fixes.

Hotfixes:

- Added OSSMETADATA file to master/develop for internal Netflix tracking.

Contributors:

- @mikegrima
- @monkeysecurity
- @OllyTheNinja-Xero
- @AlexCline

v0.4.0 (2015-11-20)
===================
- PR #228 - jeremy-h - IAM check misses '*' when found within a list. (Issue #223)
- PR #230 - markofu - New error and echo functions to simplify code for scripts/secmonkey_auto_install.sh
- PR #233 - mikegrima - Write tests for security_monkey.common.ARN (Issue #222)
- PR #238 - monkeysecurity - Refactoring _check_rfc_1918 and improving VPC ELB Internet Accessible Check
- PR #241 - bunjiboys - Seed Amazon owned AWS accounts (Issue #169)
- PR #243 - mikegrima - Fix for underscores not being detected in SNS watcher. (Issue #240)
- PR #244 - mikegrima - Setup TravisCI (Issue #227)
- PR #250 - OllyTheNinja-Xero - upgrade deprecated botocore calls in ELB watcher (Issue #249)
- PR #256 - mikegrima - Latest Boto3/botocore versions (Issue #254)
- PR #261 - bunjiboys - Add ec2:DescribeInstances to quickstart role documentation (Issue #260)
- PR #263 - monkeysecurity - Updating docs/scripts to pin to dart 1.12.2-1 (Issue #259)
- PR #265 - monkeysecurity - Remove ratelimiting max attempts, wrap ELB watcher with try/except/continue

Hotfixes:

- Issue #235 - OllyTheNinja-Xero - SNS Auditor - local variable 'entry' referenced before assignment

Contributors:

- @jeremy-h
- @mark-fu
- @mikegrima
- @bunjiboys
- @OllyTheNinja-Xero
- @monkeysecurity


v0.3.9 (2015-10-08)
===================
- PR #212 - bunjiboys - Make email failures warnings instead of debug messages
- PR #203 - markofu - Added license to secmonkey_auto_install.sh.
- PR #207 - cbarrac - Updated dependencies and dart installation for secmonkey_auto_install.sh
- PR #209 - mikegrima - Make SNS Ignorelist use name instead of ARN.
- PR #213 - Qmando - Added more exception handling to the S3 watcher.
- PR #215 - Dklotz-Circle - Added egress rules to the security group watcher.
- monkeysecurity - Updated quickstart.rst IAM policy to remove wildcards and include redshift permissions.
- PR #218 - monkeysecurity - Added exception handling to the S3 bucket.get_location API call.
- PR #221 - Qmando - Retry on AWS API error when slurping ELBs.
- monkeysecurity - Updated cryptography package from 1.0 to 1.0.2 for easier installation under OS X El Capitan.

Hotfixes:

- Updated quickstart.rst and secmonkey_auto_install.sh to remove swig/python-m2crypto and add libffi-dev
- Issue #220 - SQS Auditor not correctly parsing ARNs, halting security_monkey. Fixed by abstracting ARN parsing into a new class (security_monkey.common.arn).  Updated the SNS Auditor to also use this new class.

Contributors:

- bunjiboys
- markofu
- cbarrac
- mikegrima
- Qmando
- Dklotz-Circle
- monkeysecurity


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
