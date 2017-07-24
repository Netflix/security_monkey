Postgres on AWS
===============

Amazon can host your postgres database in their [RDS service](https://aws.amazon.com/rds/).  We recommend using AWS RDS or [GCP Cloud SQL](postgres_gcp.md) to productionalize your Security Monkey deployment.

You must create a Postgres RDS instance in the same region you intend to launch your Security Monkey instance.

Create RDS Security Group
-------------------------
The first step is to create a security group for this RDS instance. Navigate to the AWS EC2 console's security group section.
Please ensure that you are within the same region that Security Monkey is deployed in.

Click `Create Security Group`:

![Create new security group](images/new_security_group.png)

Create a new security group named `securitymonkey-rds`, and add an ingress rule on TCP 5432 to permit the `securitymonkey` 
(or whatever you named the security group that Security Monkey is launched with) security group access.

![Sg details](images/rds_sg.png)


Launch Postgres RDS Instance
---------------------------

![Create RDS Instance](images/aws_rds.png "Create RDS Instance")

The AWS supplied defaults should get you going. 
Make sure that you launch the RDS instance with the `securitymonkey-rds` security group that we created above.

You will need to use the hostname, dbname, username, password to create a `SQLALCHEMY_DATABASE_URI` for your config.

    SQLALCHEMY_DATABASE_URI = 'postgresql://securitymonkeyuser:securitymonkeypassword@hostname:5432/secmonkey'

Advanced users may wish to supply a KMS key for encryption at rest.


Next:
-----

- [Quickstart](quickstart.md#launch-an-instance)