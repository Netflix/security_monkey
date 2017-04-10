Postgres on AWS
===============

Amazon can host your postgres database in their [RDS service](https://aws.amazon.com/rds/).  We recommend using AWS RDS or [GCP Cloud SQL](postgres_gcp.md) to productionalize your security_monkey deployment.

Create a Postgres RDS instance in the same region you intend to launch your security_monkey instance.

![Create RDS Instance](images/aws_rds.png "Create RDS Instance")

The AWS supplied defaults should get you going.  You will need to use the hostname, dbname, username, password to create a SQLALCHEMY_DATABASE_URI for your config.

    SQLALCHEMY_DATABASE_URI = 'postgresql://securitymonkeyuser:securitymonkeypassword@hostname:5432/secmonkey'

Advanced users may wish to supply a KMS key for encryption at rest.

Next:
-----

- [Quickstart](quickstart.md#launch-an-instance)