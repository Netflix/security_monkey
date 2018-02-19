Quick Start Guide
=================

Setup on AWS, GCP, or OpenStack
-------------------------------

Security Monkey can run on an [Amazon EC2 (AWS)](iam_aws.md) instance, [Google Cloud Platform (GCP)](iam_gcp.md) instance (Google Cloud Platform), or [OpenStack (public or private cloud)](iam_openstack.md) instance.
The only real difference in the installation is the IAM configuration and the bringup of the Virtual Machine that runs Security Monkey.

### GitHub Organization Monitoring
For monitoring GitHub, please read the [GitHub monitoring documentation here](github_setup.md).

Installation Instructions:
-------------------
1. [Launch a server](installation/01-launch-instance.md)
2. [Create a database instance](02-create-db.md)
3. [Install Security Monkey on your server instance](03-install-sm.md)
4. [Populate your Security Monkey with Accounts](04-accounts.md)
5. [Create an SSL Certificate](05-ssl.md)
6. [Setup Nginx](06-nginx.md)
7. [Login to Security Monkey & load data](07-load-data.md)
8. [Hardening Security Monkey for Production](autostarting.md)

User Guide
----------

See the [User Guide](userguide.md) for a walkthrough of Security Monkey's features.

Contribute
----------

It's easy to extend Security Monkey with new rules or new technologies. Please read our [Contributing Documentation](contributing.md) for additional details.
