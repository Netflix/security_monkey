*********
Changelog
*********

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
