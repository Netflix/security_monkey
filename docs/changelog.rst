*********
Changelog
*********

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
