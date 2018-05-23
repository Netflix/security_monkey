Quick Start Guide
=================

Setup on AWS, GCP, or OpenStack
-------------------------------

Security Monkey can run on an [Amazon EC2 (AWS)](iam_aws.md) instance, [Google Cloud Platform (GCP)](iam_gcp.md) instance (Google Cloud Platform), or [OpenStack (public or private cloud)](iam_openstack.md) instance.
The only real difference in the installation is the IAM configuration and the bringup of the Virtual Machine that runs Security Monkey.

### GitHub Organization Monitoring
For monitoring GitHub, please read the [GitHub monitoring documentation here](github_setup.md).

### Running Security Monkey in Production
The Quickstart guide is great for learning about Security Monkey and trying it, but it is not adequate for production deployments.  If you follow the steps in Quickstart Security Monkey will not automatically scan your environment and won't scale for large accounts.  For production deployment guidance please read [Autostarting](autostarting.md) and [Tuning the Watchers/Prioritizing](tuneworkers.md) before beginning installation.

Installation Instructions:
-------------------
1. Follow the proper IAM and permissions instructions for your platform: [AWS](iam_aws.md), [GCP](iam_gcp.md), [OpenStack](iam_openstack.md), [GitHub](github_setup.md)
1. [Launch a server](installation/01-launch-instance.md)
2. [Create a database instance](installation/02-create-db.md)
3. [Install Security Monkey on your server instance](installation/03-install-sm.md)
4. [Populate your Security Monkey with Accounts](installation/04-accounts.md)
5. [Create an SSL Certificate](installation/05-ssl.md)
6. [Setup Nginx](installation/06-nginx.md)
7. [Login to Security Monkey & load data](installation/07-load-data.md)
8. [Hardening Security Monkey for Production (Autostarting)](autostarting.md)

User Guide
----------

See the [User Guide](userguide.md) for a walkthrough of Security Monkey's features.

Contribute
----------

It's easy to extend Security Monkey with new rules or new technologies. Please read our [Contributing Documentation](contributing.md) for additional details.
