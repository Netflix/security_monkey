=============
Configuration
=============

AWS Configuration
=================

In order for Security Monkey to monitor it's own account and other accounts
we must ensure it has the correct AWS permissions to do so.

There are several different ways you could do this, below detail the recommended.

Setting up IAM roles
--------------------

Security Monkey uses boto heavily to talk to all the AWS resources it monitors. By default it uses the on-instance credentials to make the necessary calls.

In order to limit the permissions (Security Monkey is a read-only) we will create a new two IAM roles for Security Monkey. You can name them whatever you would like but for example sake we will be calling them SecurityMonkeyInstanceProfile and SecurityMonkey.

Security Monkey uses to STS to talk to different accounts. For monitoring one account this isn't necessary but we will still use it so that we can easily add new accounts.

SecurityMonkeyInstanceProfile is the IAM role you will launch your instance with. It actually has almost no rights. In fact it should really only be able to use STS to assume role to the SecurityMonkey role.

Here is are example polices for the SecurityMonkeyInstanceProfile:

SES-SendEmail 

.. code-block:: python

    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "ses:SendEmail"
          ],
          "Resource": "*"
        }
      ]
    }


SM-Route53

.. code-block:: python
    
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "route53:Get*",
            "route53:List*",
                        "route53:ChangeResourceRecordSets"
          ],
          "Resource": [
            "*"
          ]
        }
      ]
    }


STS-AssumeRole

.. code-block:: python

    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": 
            "sts:AssumeRole",
          "Resource": "*"
        }
      ]
    }



Next we will create the the SecurityMonkey IAM role. This is the role that actually has access (read-only) to the different technology resources.

Here is an example policy for SecurityMonkey:

SM-ReadOnly

.. code-block:: python
    
    {
      "Statement": [
        {
          "Action": [
            "autoscaling:Describe*",
            "cloudformation:DescribeStacks",
            "cloudformation:DescribeStackEvents",
            "cloudformation:DescribeStackResources",
            "cloudformation:GetTemplate",
            "cloudfront:Get*",
            "cloudfront:List*",
            "cloudwatch:Describe*",
            "cloudwatch:Get*",
            "cloudwatch:List*",
            "directconnect:Describe*",
            "dynamodb:GetItem",
            "dynamodb:BatchGetItem",
            "dynamodb:Query",
            "dynamodb:Scan",
            "dynamodb:DescribeTable",
            "dynamodb:ListTables",
            "ec2:Describe*",
            "elasticache:Describe*",
            "elasticbeanstalk:Check*",
            "elasticbeanstalk:Describe*",
            "elasticbeanstalk:List*",
            "elasticbeanstalk:RequestEnvironmentInfo",
            "elasticbeanstalk:RetrieveEnvironmentInfo",
            "elasticloadbalancing:Describe*",
            "iam:List*",
            "iam:Get*",
            "route53:Get*",
            "route53:List*",
            "rds:Describe*",
            "s3:Get*",
            "s3:List*",
            "sdb:GetAttributes",
            "sdb:List*",
            "sdb:Select*",
            "ses:Get*",
            "ses:List*",
            "sns:Get*",
            "sns:List*",
            "sqs:GetQueueAttributes",
            "sqs:ListQueues",
            "sqs:ReceiveMessage",
            "storagegateway:List*",
            "storagegateway:Describe*"
          ],
          "Effect": "Allow",
          "Resource": "*"
        }
      ]
    }



Setting up STS access
---------------------
Once we have setup our accounts we need to ensure that we create a trust relationship so that SecurityMonkeyInstanceProfile can assume the SecurityMonkey role.

In the AWS console select the SecurityMonkey IAM role and select the Trust Relationships tab and click Edit Trust Relationship

Below is an example policy:

.. code-block:: python

    {
      "Version": "2008-10-17",
      "Statement": [
        {
          "Sid": "",
          "Effect": "Allow",
          "Principal": {
            "AWS": [
              "arn:aws:iam::<awsaccountnumber>:role/SecurityMonkeyInstanceProfile",
            ]
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }


Adding N+1 accounts
-------------------

To add another account we go to the new account and create a new SecurityMonkey IAM role with the same policy as above. 

Then we would go to the account that Security Monkey is running is and edit the trust relationship policy.

An example policy:

.. code-block:: python

    {
      "Version": "2008-10-17",
      "Statement": [
        {
          "Sid": "",
          "Effect": "Allow",
          "Principal": {
            "AWS": [
              "arn:aws:iam::<awsaccountnumber>:role/SecurityMonkeyInstanceProfile",
              "arn:aws:iam::<awsaccountnumber1>:role/SecurityMonkeyInstanceProfile",
            ]
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }


Security Monkey Configuration
=============================

Most of Security Monkey's configuration is done via the Security Monkey Configuration file see: :doc:`configuration options <./options>` for a full list of options.

The default config includes a few values that you will need to change before starting Security Monkey the first time. see: security_monkey/env-config/config-deploy.py

FQDN
----

To perform redirection security monkey needs to know the FQDN you intend to use. IF R53 is enabled this FQDN will be
automatically added to Route53 when Security Monkey starts.


SQLACHEMY_DATABASE_URI
----------------------

If you have ever used sqlalchemy before this is the standard connection string used. Security Monkey uses a postgres database and the connection string would look something like:

    SQLALCHEMY_DATABASE_URI = 'postgressql://<user>:<password>@<hostname>:5432/SecurityMonkey'

SECRET_KEY
----------

This SECRET_KEY is essential to ensure the sessions generated by Flask cannot be guessed. You must generate a RANDOM SECRET_KEY for this value.

An example of how you might generate a random string:

    >>> import random
    >>> secret_key = ''.join(random.choice(string.ascii_uppercase) for x in range(6))
    >>> secret_key = secret_key + ''.join(random.choice("~!@#$%^&*()_+") for x in range(6))
    >>> secret_key = secret_key + ''.join(random.choice(string.ascii_lowercase) for x in range(6))
    >>> secret_key = secret_key + ''.join(random.choice(string.digits) for x in range(6))


SECURITY_PASSWORD_SALT
----------------------

For many of the same reasons we want want a random SECRET_KEY we want to ensure our password salt is random. see: `Salt <http://en.wikipedia.org/wiki/Salt_(cryptography)>`_

You can use the same method used to generate the SECRET_KEY to generate the SECURITY_PASSWORD_SALT


