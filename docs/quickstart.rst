============
Introduction
============

Security Monkey monitors policy changes and alerts on insecure configurations in an AWS account. While Security Monkey's main purpose is security, it also proves a useful tool
for tracking down potential problems as it is essentially a change tracking system.

How it works
=============

When you add an AWS account:

- will periodically fetch policies for technologies such as (Security Groups, S3, IAM, SQS, ELB, etc.) for that account
- will capture that policy and create a "revision" that can be referred to at a later time
- will audit that policy to determine if the configuration is insecure
- will notify external teams about the insecure configuration and direct them to remediate or justify the issue

Key points:

- because fetching is periodic it is not guaranteed to record every change

Other features
======================

- able to view differences between revisions
- support for multiple AWS accounts
- extensible audit rules
- easily add additional technologies
- users can subscribe to change alerts

Technologies used
==================

- Python
- Flask
- Postgres
- AngularDart
- gunicorn

Known issues
============

-

Future Plans
============

- Integration with CloudTrail.  Security Monkey explains what changed. CloudTrail can explain who changed it.
- Add the ability to compare different configuration items.  This can be especially useful to ensure your cross region deployment is symmetrical.
- CSRF protections for form POSTs.
- Content Security Policy headers.
- Additional AWS technology and configuration tracking, including VPC components and S3 lifecycle configuration.
- Test integration with moto.
- Roles/authorization capabilities for admin vs. user roles

.. _securitymonkey project: https://github.com/netflix/SecurityMonkey/
.. _Python: https://en.wikipedia.org/wiki/Python_(programming_language)
.. _Flask: http://flask.pocoo.org/
.. _Bootstrap: http://twitter.github.com/bootstrap/
