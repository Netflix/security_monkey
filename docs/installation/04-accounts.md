Populate Security Monkey with Accounts
--------------------------------------

### Add Amazon Accounts (AWS ONLY)

If you don't use AWS, you can skip this section.

Security Monkey has the ability to check which accounts are accessing your resources. This is helpful to
detect if there is unknown cross-account access. In some cases, your items will be configured to permit
Amazon owned accounts that provide specific AWS services, such as ELB access logging. Security Monkey is 
equipped with a command to automatically add these accounts to the database, which will prevent Security Monkey
from raising an "unknown cross-account access" issue on a given item.

To add the "friendly" Amazon service accounts to Security Monkey, please run the command:

    monkey amazon_accounts    

### Add Your AWS/GCP Accounts

You'll need to add at least one account before starting the scheduler. It's easiest to add them from the command line, but it can also be done through the web UI. :

    monkey add_account_aws
    usage: monkey add_account_aws [-h] -n NAME [--thirdparty] [--active]
                                  [--notes NOTES] --id IDENTIFIER
                                  [--update-existing]
                                  [--canonical_id CANONICAL_ID]
                                  [--s3_name S3_NAME] [--role_name ROLE_NAME]

    monkey add_account_gcp
    usage: monkey add_account_gcp [-h] -n NAME [--thirdparty] [--active]
                                  [--notes NOTES] --id IDENTIFIER
                                  [--update-existing] [--creds_file CREDS_FILE]

    monkey add_account_openstack
    usage: monkey add_account_openstack [-h] -n NAME [--thirdparty] [--active]
                                  [--notes NOTES] --id IDENTIFIER
                                  [--update-existing]
                                  [--cloudsyaml_file CLOUDSYAML_FILE]

For clarity: the `-n NAME` refers to the name that you want Security Monkey to use to associate with the account.
A common example would be "test" for your testing AWS account or "prod" for your main production AWS account. These names are unique.
Note that `--role_name` defaults to "SecurityMonkey", if you are using a different role, this value is just the role name, not the ARN.

The `--id IDENTIFIER` is the back-end cloud service identifier for a given provider. For AWS, it's the 12 digit account number, 
and for GCP, it's the project ID. For OpenStack, it's the cloud configuration to load from the clouds.yaml file.

### Syncing With SWAG

If you're using [SWAG](https://github.com/Netflix-Skunkworks/swag-client). You can populate your database via the following command:

    monkey sync_swag --owner <example-corp> --bucket-name <my-bucket> --bucket-prefix accounts.json --bucket-region us-east-1 -u


### AWS Only: S3 Canonical IDs

If you are not using AWS, you can skip this section. If you are using AWS, you should run the command (this command should
be run on the Security Monkey instance or otherwise in a place with AWS credentials. For more details, please review the
[AWS IAM instructions](../iam_aws.md)):
    
    monkey fetch_aws_canonical_ids
    usage: monkey fetch_aws_canonical_ids [-h] [--override OVERRIDE]

    Adds S3 canonical IDs in for all AWS accounts in SM.
    
    optional arguments:
      -h, --help           show this help message and exit
      --override OVERRIDE

AWS S3 has an ACL system that makes use of Canonical IDs. This is documented [here](http://docs.aws.amazon.com/general/latest/gr/acct-identifiers.html).
These IDs are not easy to find, but are very important for Security Monkey to know if an S3 bucket has unknown cross-account access.
The above command is a convenience to automatically find those Canonical IDs and associate them with your account. It is highly recommended that you run this command after you add an AWS account.

### Create the first user:

Users can be created on the command line or by registering in the web UI:

    $ monkey create_user "you@youremail.com" "Admin"
    > Password:
    > Confirm Password:

`create_user` takes two parameters:
- email address
- role (One of `[View, Comment, Justify, Admin]`)

--
### Next step: [Create an SSL Certificate](05-ssl.md)
--