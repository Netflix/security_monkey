Security Monkey
===============

<img align="right" alt="Security Monkey Logo 2017" src="docs/images/Security_Monkey.png" width="50%">

Security Monkey monitors your [AWS and GCP accounts](https://medium.com/@Netflix_Techblog/netflix-security-monkey-on-google-cloud-platform-gcp-f221604c0cc7) for policy changes and alerts on insecure configurations.  Support is available for OpenStack public and private clouds.  It provides a single UI to browse and search through all of your accounts, regions, and cloud services.  The monkey remembers previous states and can show you exactly what changed, and when.

Security Monkey can be extended with [custom account types](docs/plugins.md), [custom watchers](docs/development.md#adding-a-watcher), [custom auditors](docs/development.md#adding-an-auditor), and [custom alerters](docs/misc.md#custom-alerters).

It works on CPython 2.7. It is known to work on Ubuntu Linux and OS X.

[![Stories in Ready](https://badge.waffle.io/Netflix/security_monkey.svg?label=ready&title=Ready)](http://waffle.io/Netflix/security_monkey) [![Gitter chat](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/Netflix/security_monkey)

| Develop Branch  | Master Branch |
| ------------- | ------------- |
| [![Build Status](https://travis-ci.org/Netflix/security_monkey.svg?branch=develop)](https://travis-ci.org/Netflix/security_monkey)  | [![Build Status](https://travis-ci.org/Netflix/security_monkey.svg?branch=master)](https://travis-ci.org/Netflix/security_monkey)  |
| [![Coverage Status](https://coveralls.io/repos/github/Netflix/security_monkey/badge.svg?branch=develop)](https://coveralls.io/github/Netflix/security_monkey?branch=develop)  | [![Coverage Status](https://coveralls.io/repos/github/Netflix/security_monkey/badge.svg?branch=master)](https://coveralls.io/github/Netflix/security_monkey?branch=master) |


Project resources
-----------------

- [Quickstart](docs/quickstart.md)
- [Upgrading](docs/update.md)
- [Changelog](docs/changelog.md)
- [Source code](https://github.com/netflix/security_monkey)
- [Issue tracker](https://github.com/netflix/security_monkey/issues)
- [Gitter.im Chat Room](https://gitter.im/Netflix/security_monkey)
- [CloudAux](https://github.com/Netflix-Skunkworks/cloudaux)
- [PolicyUniverse](https://github.com/Netflix-Skunkworks/policyuniverse)


Instance Diagram
---------------
The components that make up Security Monkey are as follows (not AWS specific):
![diagram](docs/images/sm_instance_diagram.png)


Access Diagram
------------
Security Monkey accesses accounts to scan via credentials it is provided ("Role Assumption" where available).
![diagram](docs/images/sm_iam_diagram.png)
