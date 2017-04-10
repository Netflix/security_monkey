Configuration
=============

IAM Permissions
---------------

-   For AWS, please see [AWS IAM instructions](iam_aws.md).
-   For GCP, please see [GCP IAM instructions](iam_gcp.md).

Database
--------

Security Monkey needs a postgres database. Select one of the following:

-   [Postgres on AWS RDS](postgres_aws.md).
-   [Postgres on GCP's Cloud SQL](postgres_gcp.md).

Security Monkey Configuration
-----------------------------

Most of Security Monkey's configuration is done via the Security Monkey Configuration file see: configuration [options](options.md) for a full list of options.

The default config includes a few values that you will need to change before starting Security Monkey the first time. see: `security_monkey/env-config/config.py`
