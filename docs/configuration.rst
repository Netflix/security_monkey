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
          "Action": "sts:AssumeRole",
          "Resource": "arn:aws:iam::*:role/SecurityMonkey"
        }
      ]
    }



Next we will create the the SecurityMonkey IAM role. This is the role that actually has access (read-only) to the different technology resources.

Here is an example policy for SecurityMonkey:

SM-ReadOnly

.. code-block:: json

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "ec2:describeaddresses",
                    "ec2:describedhcpoptions",
                    "ec2:describeinstances",
                    "ec2:describeinternetgateways",
                    "ec2:describekeypairs",
                    "ec2:describeregions",
                    "ec2:describeroutetables",
                    "ec2:describesecuritygroups",
                    "ec2:describesubnets",
                    "ec2:describetags",
                    "ec2:describevpcs",
                    "elasticloadbalancing:describeinstancehealth",
                    "elasticloadbalancing:describeloadbalancerattributes",
                    "elasticloadbalancing:describeloadbalancerpolicies",
                    "elasticloadbalancing:describeloadbalancers",
                    "iam:getgroup",
                    "iam:getgrouppolicy",
                    "iam:getloginprofile",
                    "iam:getpolicyversion",
                    "iam:getrole",
                    "iam:getrolepolicy",
                    "iam:getservercertificate",
                    "iam:getuser",
                    "iam:getuserpolicy",
                    "iam:listaccesskeys",
                    "iam:listattachedrolepolicies",
                    "iam:listentitiesforpolicy",
                    "iam:listgrouppolicies",
                    "iam:listgroups",
                    "iam:listinstanceprofilesforrole",
                    "iam:listmfadevices",
                    "iam:listpolicies",
                    "iam:listrolepolicies",
                    "iam:listroles",
                    "iam:listservercertificates",
                    "iam:listsigningcertificates",
                    "iam:listuserpolicies",
                    "iam:listusers",
                    "redshift:DescribeClusters",
                    "rds:describedbsecuritygroups",
                    "route53:listhostedzones",
                    "route53:listresourcerecordsets",
                    "s3:getbucketacl",
                    "s3:getbucketcors",
                    "s3:getbucketlocation",
                    "s3:getbucketlogging",
                    "s3:getbucketpolicy",
                    "s3:getbucketversioning",
                    "s3:getlifecycleconfiguration",
                    "s3:listallmybuckets",
                    "ses:getidentitydkimattributes",
                    "ses:getidentitynotificationattributes",
                    "ses:getidentityverificationattributes",
                    "ses:listidentities",
                    "ses:listverifiedemailaddresses",
                    "ses:sendemail",
                    "sns:gettopicattributes",
                    "sns:listsubscriptionsbytopic",
                    "sns:listtopics",
                    "sqs:getqueueattributes",
                    "sqs:listqueues",
                    "sqs:receivemessage",
                    "es:DescribeElasticSearchDomainConfig",
                    "es:ListDomainNames"
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
              "arn:aws:iam::*:role/SecurityMonkeyInstanceProfile",
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


