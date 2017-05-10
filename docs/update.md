Update Security Monkey
======================

Update Security Monkey on your Instance
----------------------------------------

Update Steps:

-   Prerequisites
-   Backup and stop services
-   Clone security_monkey and update environment
-   Compile (or download) the web UI
-   Update database and configurations
-   Start services

### Prerequisites

This doc assumes you already have installed and running security monkey environment. Especially it assumes you have following on your system
1. https://github.com/Netflix/security_monkey project files are available under /usr/local/src/security_monkey
2. [Supervisor](http://supervisord.org/) configured and running
3. Python virtualenv

### Backup config and installation files

Backup your `/usr/local/src/security_monkey/env-config/config.py` and move your exsiting installation to backup directory
```
cp /usr/local/src/security_monkey/env-config/config.py ~/
mkdir ~/security_monkey_backup && mv /usr/local/src/security_monkey/ ~/security_monkey_backup/
```

### Stop services

Stop securitymonkey and the scheduler services using supervisorctl.
```
sudo supervisorctl stop securitymonkey
sudo supervisorctl stop securitymonkeyscheduler
```

### Clone security_monkey

Releases are on the master branch and are updated about every three months. Bleeding edge features are on the develop branch.
git clone https://github.com/Netflix/security_monkey.git into the your security monkey location
```
$ cd /usr/local/src
$ sudo git clone --depth 1 --branch develop https://github.com/Netflix/security_monkey.git
```


### Update Python environment

Activate your python virtualenv and run python setup.py install
```
cd security_monkey
virtualenv venv
source venv/bin/activate
pip install --upgrade setuptools
pip install google-compute-engine  # Only required on GCP
python setup.py install
```

### Compile (or Download) the web UI
If you're using the stable (master) branch, you have the option of downloading the web UI instead of compiling it. Visit the latest release <https://github.com/Netflix/security_monkey/releases/latest> and download static.tar.gz.

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

Security Monkey uses Flask-Migrate (Alembic) to keep database tables up to date. To update the tables, run this command.
Note: python manage.py db upgrade is idempotent. You can re-run it without causing any harm.

```
cd /usr/local/src/security_monkey/
monkey db upgrade
```

### Start services
```
sudo supervisorctl start securitymonkey
sudo supervisorctl start securitymonkeyscheduler
```
*Note:*
*Netflix doesn't upgrade/patch Security Monkey systems. Instead simply rebake a new instance with the new version.*
