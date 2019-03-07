Update Security Monkey
======================
This documents how to perform a proper upgrade of the Security Monkey instance.

🚨⚠️🥁🎺 PLEASE READ: BREAKING CHANGES FOR 1.0 🎺🥁⚠️🚨
--------------
If you are an existing user of Security Monkey (version before 1.0), please read this section as there are breaking changes in the
1.0 version of Security Monkey.

If you are upgrading to 1.0 for the first time, please review the [Quickstart](quickstart.md) and the [Autostarting](autostarting.md)
documents as there is a new deployment pattern for Security Monkey.

### What changed?
Security Monkey now has the ability to scale workers horizontally thanks to Celery. This changes the deployment story for
Security Monkey, and also changes how the scheduling of tasks works. This is documented in the [autostarting](autostarting.md)
file. Please read this file as it explains the 1.0+ architecture.

Security Monkey now has 5 primary components:
1. UI (Can have many behind a load balancer)
1. Scheduler (EXACTLY ONE)
1. Workers (Can have many)
1. PostgreSQL Database (for storage)
1. Redis (message broker for workers)

Also, (for AWS) please review the [IAM documentation](https://github.com/Netflix/security_monkey/blob/develop/docs/iam_aws.md) as there are new permissions required.


General Deployment Guidance:
------------------
As a general guidance, the deployment of Security Monkey should follow these steps:
1. Deploy the UI behind a Load Balancer
1. Tear-down the scheduler instance
1. Tear-down all worker instances
1. *At this point, you should perform any database migrations and upgrades as there are no workers that will be affected.*
1. Deploy the new scheduler instance -- wait for it to come online
1. Deploy many worker instances

Performing the steps in this order will ensure:
- That no duplicate schedulers are running (multiple schedulers running causes havoc)
- Proper DB upgrades occur without possibly impacting workers mutating the database
- The schedulers and workers are working properly together


Update Steps:
-----------
-   Prerequisites
-   Backup and stop services
-   Clone `security_monkey` and update environment
-   Compile (or download) the web UI
-   Tear down scheduler and workers
-   Update database and configurations
-   Start services (Start UI first, then the scheduler, then the workers)

### Prerequisites

This doc assumes you already have installed and are running a Security Monkey environment. It especially assumes you have following on your system
1. https://github.com/Netflix/security_monkey project files are available under /usr/local/src/security_monkey
1. [Supervisor](http://supervisord.org/) configured and running
1. Python virtualenv
1. Redis
1. NGINX

## Update the Security Monkey IAM permissions (if applicable):

As new features come out, Security Monkey may require new IAM permissions. Always follow the [respective IAM doc for the given technology](https://github.com/Netflix/security_monkey/blob/develop/docs/quickstart.md#account-types)
to see if you need to update your Security Monkey permissions. Failure to do this will result in Access Denied errors and items not appearing in Security Monkey.

### Backup config and installation files

Backup your `/usr/local/src/security_monkey/env-config/config.py` and move your existing installation to backup directory

```
cp /usr/local/src/security_monkey/env-config/config.py ~/
mkdir ~/security_monkey_backup && mv /usr/local/src/security_monkey/ ~/security_monkey_backup/
```

### Stop services

Stop all Security Monkey services using `supervisorctl`.

```
sudo supervisorctl stop securitymonkeyui
sudo supervisorctl stop securitymonkeyscheduler
sudo supervisorctl stop securitymonkeyworkers
```

### Clone `security_monkey`

Major releases are on the `master` branch. Please be aware that these releases happen slowly over time. If you require the latest and greatest features (as well as bug fixes), please checkout the `develop` branch.
`git clone https://github.com/Netflix/security_monkey.git` into the your Security Monkey location

```
$ cd /usr/local/src
$ sudo git clone --depth 1 --branch develop https://github.com/Netflix/security_monkey.git
```

### Update Python environment

Activate your Python `virtualenv` and run `pip install -e .`
```
cd security_monkey
virtualenv venv
source venv/bin/activate
pip install --upgrade setuptools
pip install --upgrade pip
pip install --upgrade urllib3[secure]   # to prevent InsecurePlatformWarning
pip install google-compute-engine  # Only required on GCP
pip install oauth2client # Required to retrieve GCP data
pip install google-api-python-client # Required to retrieve GCP data
pip install httplib2 # Required to retrieve GCP data
pip install cloudaux\[gcp\]
pip install cloudaux\[openstack\]    # Only required on OpenStack
pip install -e .
pip install -e ."[tests]"
```

### Compile (or Download) the web UI
If you're using the stable (master) branch, you have the option of downloading the web UI instead of compiling it. Visit the latest release <https://github.com/Netflix/security_monkey/releases/latest> and download `static.tar.gz`.

If you're using the bleeding edge (develop) branch, you will need to compile the web UI by following these instructions.
If you have not done this during installation follow [this](quickstart.md#compile-or-download-the-web-ui) section in [quickstart](quickstart.md) guide

Compile the web-app from the Dart code

#### Build the Web UI
```
cd /usr/local/src/security_monkey/dart
sudo /usr/lib/dart/bin/pub get
sudo /usr/lib/dart/bin/pub build
```

#### Copy the compiled Web UI to the appropriate destination

```
mkdir -p /usr/local/src/security_monkey/security_monkey/static/
/bin/cp -R /usr/local/src/security_monkey/dart/build/web/* /usr/local/src/security_monkey/security_monkey/static/
chgrp -R www-data /usr/local/src/security_monkey
```

### Update configurations

Replace the config file that we previously backed up.

```
sudo mv ~/config.py /usr/local/src/security_monkey/env-config/
```

If your file is named something other than `config.py`, you will want to set the `SECURITY_MONKEY_SETTINGS` environment variable to point to your config:

```
export SECURITY_MONKEY_SETTINGS=/usr/local/src/security_monkey/env-config/config-deploy.py
```

### Update the database tables

Security Monkey uses Flask-Migrate (Alembic) to keep database tables up to date. To update the tables, run this command (while
in your virtual environment):
Note: `monkey db upgrade` is [idempotent](https://www.google.com/search?safe=active&q=Dictionary#dobs=Idempotent). You can re-run it without causing any harm.

```
cd /usr/local/src/security_monkey/
monkey db upgrade
```

### Start services
```
sudo supervisorctl start securitymonkeyui
sudo supervisorctl start securitymonkeyscheduler
sudo supervisorctl start securitymonkeyworkers
```
*Note:*
*Netflix doesn't upgrade/patch Security Monkey systems. Instead simply rebake a new instance with the new version.*
