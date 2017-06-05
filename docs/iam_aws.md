IAM Role Setup on AWS
=====================

We need to create two roles for security monkey. The first role will be an instance profile that we will launch security monkey into. The permissions on this role allow the monkey to use STS to assume to other roles as well as use SES to send email.

Creating SecurityMonkeyInstanceProfile Role
-------------------------------------------

Create a new role and name it "SecurityMonkeyInstanceProfile":

![image](images/resized_name_securitymonkeyinstanceprofile_role.png)

Select "Amazon EC2" under "AWS Service Roles".

![image](images/resized_create_role.png)

Select "Custom Policy":

![image](images/resized_role_policy.png)

Paste in this JSON with the name "SecurityMonkeyLaunchPerms":

~~~~ {.sourceCode .json}
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/SecurityMonkey"
    }
  ]
}
~~~~

Review and create your new role:

![image](images/resized_role_confirmation.png)

Creating SecurityMonkey Role
----------------------------

Create a new role and name it "SecurityMonkey":

![image](images/resized_name_securitymonkey_role.png)

Select "Amazon EC2" under "AWS Service Roles".

![image](images/resized_create_role.png)

Select "Custom Policy":

![image](images/resized_role_policy.png)

Paste in this JSON with the name "SecurityMonkeyReadOnly":

~~~~ {.sourceCode .json}
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "acm:describecertificate",
                "acm:listcertificates",
                "cloudtrail:describetrails",
                "cloudtrail:gettrailstatus",
                "config:describeconfigrules",
                "config:describeconfigurationrecorders",
                "directconnect:describeconnections",
                "ec2:describeaddresses",
                "ec2:describedhcpoptions",
                "ec2:describeflowlogs",
                "ec2:describeimages",
                "ec2:describeinstances",
                "ec2:describeinternetgateways",
                "ec2:describekeypairs",
                "ec2:describenatgateways",
                "ec2:describenetworkacls",
                "ec2:describenetworkinterfaces",
                "ec2:describeregions",
                "ec2:describeroutetables",
                "ec2:describesecuritygroups",
                "ec2:describesnapshots",
                "ec2:describesubnets",
                "ec2:describetags",
                "ec2:describevolumes",
                "ec2:describevpcendpoints",
                "ec2:describevpcpeeringconnections",
                "ec2:describevpcs",
                "ec2:describevpnconnections",
                "ec2:describevpngateways",
                "elasticloadbalancing:describeloadbalancerattributes",
                "elasticloadbalancing:describeloadbalancerpolicies",
                "elasticloadbalancing:describeloadbalancers",
                "elasticloadbalancing:describelisteners",
                "elasticloadbalancing:describerules",
                "elasticloadbalancing:describesslpolicies",
                "elasticloadbalancing:describetags",
                "elasticloadbalancing:describetargetgroups",
                "elasticloadbalancing:describetargetgroupattributes",
                "elasticloadbalancing:describetargethealth",
                "es:describeelasticsearchdomainconfig",
                "es:listdomainnames",
                "iam:getaccesskeylastused",
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
                "iam:listattachedgrouppolicies",
                "iam:listattachedrolepolicies",
                "iam:listattacheduserpolicies",
                "iam:listentitiesforpolicy",
                "iam:listgrouppolicies",
                "iam:listgroups",
                "iam:listinstanceprofilesforrole",
                "iam:listmfadevices",
                "iam:listpolicies",
                "iam:listrolepolicies",
                "iam:listroles",
                "iam:listsamlproviders",
                "iam:listservercertificates",
                "iam:listsigningcertificates",
                "iam:listuserpolicies",
                "iam:listusers",
                "kms:describekey",
                "kms:getkeypolicy",
                "kms:getkeyrotationstatus",
                "kms:listaliases",
                "kms:listgrants",
                "kms:listkeypolicies",
                "kms:listkeys",
                "lambda:listfunctions",
                "rds:describedbclusters",
                "rds:describedbclustersnapshots",
                "rds:describedbinstances",
                "rds:describedbsecuritygroups",
                "rds:describedbsnapshots",
                "rds:describedbsubnetgroups",
                "redshift:describeclusters",
                "route53:listhostedzones",
                "route53:listresourcerecordsets",
                "route53domains:listdomains",
                "route53domains:getdomaindetail",
                "s3:getaccelerateconfiguration",
                "s3:getbucketacl",
                "s3:getbucketcors",
                "s3:getbucketlocation",
                "s3:getbucketlogging",
                "s3:getbucketnotification",
                "s3:getbucketpolicy",
                "s3:getbuckettagging",
                "s3:getbucketversioning",
                "s3:getbucketwebsite",
                "s3:getlifecycleconfiguration",
                "s3:listbucket",
                "s3:listallmybuckets",
                "s3:getreplicationconfiguration",
                "s3:getanalyticsconfiguration",
                "s3:getmetricsconfiguration",
                "s3:getinventoryconfiguration",
                "ses:getidentityverificationattributes",
                "ses:listidentities",
                "ses:listverifiedemailaddresses",
                "ses:sendemail",
                "sns:gettopicattributes",
                "sns:listsubscriptionsbytopic",
                "sns:listtopics",
                "sqs:getqueueattributes",
                "sqs:listqueues"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}
~~~~

Review and create the new role.

Allow SecurityMonkeyInstanceProfile to AssumeRole to SecurityMonkey
-------------------------------------------------------------------

You should now have two roles available in your AWS Console:

![image](images/resized_both_roles.png)

Select the "SecurityMonkey" role and open the "Trust Relationships" tab.

![image](images/resized_edit_trust_relationship.png)

Edit the Trust Relationship and paste this in:

~~~~ {.sourceCode .json}
{
  "Version": "2008-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::<YOUR ACCOUNTID GOES HERE>:role/SecurityMonkeyInstanceProfile"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
~~~~

Adding more accounts
--------------------

To have your instance of security monkey monitor additional accounts, you must add a SecurityMonkey role in the new account. Follow the instructions above to create the new SecurityMonkey role. The Trust Relationship policy should have the account ID of the account where the security monkey instance is running.

**Note**

Additional SecurityMonkeyInstanceProfile roles are not required. You only need to create a new SecurityMonkey role.

**Note**

You will also need to add the new account in the Web UI, and restart the scheduler. More information on how do to this will be presented later in this guide.

Next:
-----

- [Back to the Quickstart](quickstart.md#database)