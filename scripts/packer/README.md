# SecurityMonkey Image Builder
This folder contains the necessary build scripts to generate Amazon EC2 Images (AMIs) for production environments or VirtualBox (OVF) machines for testing purposes.

## Requirements
Before we get started you need to make sure you have the following software and information available on the machine you intend to run the build process on.

* packer
    * Instructions and links to downloads can be found at https://packer.io/downloads.html
    * Installation Methods can be found at https://www.packer.io/docs/installation.html
* VirtualBox - If you want to test using a local machine (much faster for rapid iteration than AMIs). Installer can be found at https://www.virtualbox.org/
* A base Ubuntu image that has a user (vagrant/vagrant) which can SSH and sudo. Image also requires curl to be installed.
* AWS API keys - For generating AMI's you need a pair of AWS Access and Secret keys with the appropriate permissions. https://www.packer.io/docs/builders/amazon.html contains a list of the permissions required for packer.

## Building an image / machine
To build a new image is fairly trivial. Once you have cloned this repo, you will have a 3 folders and a json file.

### files directory
```
files/
├── config.py
├── nginx-nossl.conf
├── nginx-ssl.conf
└── supervisor.conf
```
* `config.py` - template for the application configuration. Will be installed as env-config/config-deploy.py
* `nginx-(ssl|nossl).conf` - the configuration files used for nginx, depending on whether or not SSL has been enabled
* `supervisor.conf` - template for supervisor

### scripts directory
```
scripts/
└── install_securitymonkey.sh
```
* `install_securitymonkey.sh` - the main build script which handles doing the actual installation

### variables directory
```
variables/
└── example.json
````
This folder contains an example of the variables JSON file required to pass in variables for the installer script. Variables in packer can either be loaded from a file like the `example.json` or they can be passed in through the command line when running packer or a mix between file and command line arguments. Any arguments passed in through the command line will override both the variables file passed in as well as default values in the main packer build script

### build.json
This is the main build definition for packer which is where we define what and how to build.

### Building an image
To build a new version of SecurityMonkey (either AMI or OVA) all you need to do is run the following command, if you have all the variables setup in the file you are passing in.

```bash
packer build -only <builder-type> -var-file variables/dev_variables.json securitymonkey_build.json
```
The `-only <builder-type>` describes what type of machine you intend to build. This must be one of either `virtualbox-ovf` or `amazon-ebs`. If you do not supply the `-only` argument, the script will attempt to build both an AMI and an OVA image.

### Overriding variables
You can as previously mentioned also override configuration variables from the command line. For example if you want to override the database password while building an Amazon AMI you would run the following command:

```bash
packer build -only ami -var-file variables/production.json \
   -var 'db_password=verysekritpassword' build.json
```

## Variables
This sections goes over all the available settings to tweak as well as their default values.

* `aws_access_key` - Access Key ID to use. Default: `AWS_ACCESS_KEY_ID` environment variable
* `aws_secret_key` - Secret Key ID to use. Default: `AWS_SECRET_ACCESS_KEY` environment variable
* `install_base_dir` - Root folder to install to. Default: `/opt`
* `tmp_base_dir` - Base folder for temporary files during installation, will be created if missing. Must be writable by the default ssh user. Default: `/tmp/secmonkey-install`
* `ec2_region` - EC2 Region to build AMI in. Default: `us-west-2`
* `ec2_source_ami` - AMI to use as base image. Default: `ami-5189a661` (Ubuntu 14.04LTS)
* `ec2_vpc_id` - ID of the VPC to launch the build instance into or default VPC if left blank. Default: *blank*
* `ec2_subnet_id` - ID of the subnet to launch the build instance into or default subnet if left blank. Default: *blank*
* `environment` - Environment to build for. Default: `ec2`
* `fqdn` - FQDN of the web frontend. Default: `securitymonkey.company.tld` **IMPORTANT**
* `api_port` - Listen port for API backend. Default: `5000`
* `base_url_format` - Format of the URL used for redirects etc. Default: `https://{}/`
* `log_dir` - Base folder for log files. Default: `/var/log/security_monkey`
* `log_file` - Main log file for API server. Combines with `log_dir` to give full path. Default: `security_monkey-deploy.log`
* `log_level` - Default log level of the application. Default: `INFO`
* `use_route53` - Update Route53 records dynamically at launch. Default: `False`
* `use_nginx` - Use nginx frontend for requests. Default: `True`
* `nginx_port` - Listen port for nginx. Default: `443`
* `nginx_ssl_enabled` - Use SSL endpoint for nginx. Default: `True`
* `nginx_ssl_self_signed` - Automatically generate a self-signed certificate for nginx. Default: `True`
* `nginx_ssl_self_signed_subj` - Subject for SSL certificate generated. Default: `/C=US/ST=CA/O=Company/localityName=Los Angeles/commonName=secmonkey/organizationalUnitName=Operations/emailAddress=security@company.tld`
* `nginx_ssl_cert_data` - Base64 encoded string of certficate data. Used only if self signed certs are disabled. Default: *blank*
* `nginx_ssl_key_data` - Base64 encoded string of certificate key. Used only if self signed certs are disabled. Default: *blank*
* `web_path` - Path to the static HTML code. Default: `/static/ui.html`
* `web_port` - Listen port for web server if nginx is disabled. Default: `443`
* `core_threads` - Max number of persistent worker threads. Default: `25`
* `max_threads` - Max number of total worker threads. Default: `30`
* `db_endpoint` - Endpoint (host:port) for database server. Default: `localhost:5432`
* `db_schema` - Name of the DB schema. Default: `secmonkey`
* `db_username` - Database username. Default: `secmonkey`
* `db_password` - Database password. Default: `CHANGEME`  **IMPORTANT**
* `db_max_overflow` - SQLAlchemy connections that can be created after poool max size is reached. Default: `15`
* `db_pool_size` - SQLAlchemy connect pool size. Default: `50`
* `mail_default_sender` - The sender (From) address used on emails sent from Security Monkey. Default: `secmonkey@company.tld`
* `mail_ses_region` - SES Region to connect to. Default: `us-west-2`
* `mail_use_smtp` - Use SMTP instead of SES. Default: `False`
* `mail_use_ssl` - If using SMTP, use an SSL connection. Default: `True`
* `mail_server` - SMTP Server. Default: `mail.company.tld`
* `mail_username` - SMTP Username. Default: `username`
* `mail_password` - SMTP Password. Default: `password`
* `secret_key` - Flask Secret key. Used to encrypt sessions. Default: `CHANGEME` **IMPORTANT**
* `sec_pw_hash` - Password hash algorithm. Default: `bcrypt`
* `sec_pw_salt` - Salt used for hashing passwords. Default: `CHANGEME` **IMPORTANT**
* `sec_confirm` - Require new users to be confirmed via email. Default: `True`
* `sec_recover` - Allow account recovery via email. Default: `True`
* `sec_register` - Allow new users to register. Default: `True`
* `sec_team_emails` - Comma-separated quoted list of email recipients for notifications. Default: `'security@company.tld', 'noc@company.tld'`
* `wtf_csrf_enabled` - Enabled Flask-WTF CSRF protection. Default: `True`
* `wtf_csrf_strict` - Enable strict referer CSRF protection. Default: `True`
* `wtf_csrf_methods` - Methods enabled for CSRF proection. Default: `'DELETE', 'POST', 'PUT', 'PATCH'`

The vast majority of these settings should be left at their default values. Some items have been marked with **IMPORTANT**, meaning that the default values should never be used for anything other than local development work at best but ideally never be used at all.

### Example variables file for building
```json
{
    "fqdn": "secmonkey.example.com",
    "log_level": "INFO",
    "ec2_vpc_id": "vpc-1a2b3c4d",
    "ec2_subnet_id": "subnet-f9e8d7c6",
    "ec2_source_ami": "ami-5892df",

    "db_endpoint": "secmonkey.randomstring.us-west-2.rds.amazonaws.com:5432",
    "db_schema": "secmonkey",
    "db_username": "secmonkey",
    "db_password": "very long and secure password goes here",

    "mail_default_sender": "soc@example.com",
    "mail_ses_region": "us-west-2",

    "secret_key": "random string",
    "sec_pw_salt": "another random string",
    "sec_team_emails": "'security-notifications@example.com'"
}
```
