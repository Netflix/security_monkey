Install Security Monkey on your Instance
----------------------------------------

Installation Steps:

-   Prerequisites
-   Setup a local postgres server
-   Clone security_monkey
-   Compile (or Download) the web UI
-   Review the config

### Prerequisites

Create the logging folders:

    sudo mkdir /var/log/security_monkey
    sudo mkdir /var/www
    sudo chown -R `whoami`:www-data /var/log/security_monkey/
    sudo chown www-data /var/www

You need to enable the `universe` repository:

    sudo add-apt-repository universe

Next, we install the tools we need for Security Monkey:

    sudo apt update
    sudo apt install -y python3 python3-dev python3-venv postgresql postgresql-contrib libpq-dev nginx supervisor git libffi-dev gcc redis-server

### Local Postgres

If you're not ready to setup AWS RDS or Cloud SQL, follow these instructions to setup a local postgres DB.

Install Postgres:

    sudo apt install postgresql postgresql-contrib

Configure the DB:

    sudo -u postgres psql
    CREATE DATABASE "secmonkey";
    CREATE ROLE "securitymonkeyuser" LOGIN PASSWORD 'securitymonkeypassword';
    CREATE SCHEMA secmonkey;
    GRANT Usage, Create ON SCHEMA "secmonkey" TO "securitymonkeyuser";
    set timezone TO 'GMT';
    select now();
    \q

### Clone security_monkey

Releases are on the master branch and are updated about every three months. Bleeding edge features are on the develop branch.

    cd /usr/local/src
    sudo git clone --depth 1 --branch develop https://github.com/Netflix/security_monkey.git
    sudo chown -R `whoami`:www-data /usr/local/src/security_monkey
    cd security_monkey
    export LC_ALL="en_US.UTF-8"
    export LC_CTYPE="en_US.UTF-8"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade setuptools
    pip install --upgrade pip
    pip install --upgrade urllib3[secure]   # to prevent InsecurePlatformWarning
    pip install -r requirements.txt
    pip install google-compute-engine  # Only required on GCP
    pip install oauth2client # Required to retrieve GCP data
    pip install google-api-python-client # Required to retrieve GCP data
    pip install httplib2 # Required to retrieve GCP data
    pip install cloudaux\[gcp\]
    pip install cloudaux\[openstack\]    # Only required on OpenStack
    pip install .

### 🚨⚠️🥁🎺 ULTRA SUPER IMPORTANT SPECIAL NOTE PLEASE READ THIS 🎺🥁⚠️🚨 ###

In the commands above, a [Python virtual environment](http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/) is created.
**ALL** Security Monkey commands from this point forward **MUST** be done from within the virtual environment. If following
the instructions above, you can get back into the virtual environment by running the following commands:

    cd /usr/local/src/security_monkey
    source venv/bin/activate


### Compile (or Download) the web UI

If you're using the stable (master) branch, you have the option of downloading the web UI instead of compiling it. Visit the latest release <https://github.com/Netflix/security_monkey/releases/latest> and download static.tar.gz.

If you're using the bleeding edge (develop) branch, you will need to compile the web UI by following these instructions:

    # Get the Google Linux package signing key.
    cd ~
    curl https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    curl --output ./dart_1.23.0-1_amd64.deb https://storage.googleapis.com/download.dartlang.org/linux/debian/pool/main/d/dart/dart_1.23.0-1_amd64.deb
    sudo dpkg -i dart_1.23.0-1_amd64.deb

    # Build the Web UI
    cd /usr/local/src/security_monkey/dart
    /usr/lib/dart/bin/pub get
    /usr/lib/dart/bin/pub build

    # Copy the compiled Web UI to the appropriate destination
    sudo mkdir -p /usr/local/src/security_monkey/static/
    sudo /bin/cp -R /usr/local/src/security_monkey/dart/build/web/* /usr/local/src/security_monkey/static/
    sudo chgrp -R www-data /usr/local/src/security_monkey
    cd /usr/local/src/security_monkey

### Configure the Application

Security Monkey ships with a config for this quickstart guide called config.py. You can override this behavior by setting the `SECURITY_MONKEY_SETTINGS` environment variable.

Modify `env-config/config.py`:
- `FQDN`: Add the IP or DNS entry of your instance.
- `SQLALCHEMY_DATABASE_URI`: This config assumes that you are using the local db option. If you setup AWS RDS or GCP Cloud SQL as your database, you will need to modify the SQLALCHEMY_DATABASE_URI to point to your DB.
- `SECRET_KEY`: Something random.
- `SECURITY_PASSWORD_SALT`: Something random.

For an explanation of the configuration options, see [options](../options.md).

### Create the database tables:

Security Monkey uses Flask-Migrate (Alembic) to keep database tables up to date. To create the tables, run this command:

    cd /usr/local/src/security_monkey/
    export SECURITY_MONKEY_SETTINGS=/usr/local/src/security_monkey/env-config/config.py  # Or your own custom path
    monkey db upgrade

--
### Next step: [Populate your Security Monkey with Accounts](04-accounts.md)
--
