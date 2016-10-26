#!/bin/bash

sudo -u postgres psql -h postgres --command "ALTER USER postgres with PASSWORD 'securitymonkeypassword';"
sudo -u postgres createdb -h postgres -O postgres secmonkey

cd /usr/local/src/security_monkey
sed -i s/localhost/postgres/ env-config/config-deploy.py
export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-deploy.py
mkdir -p /var/log/security_monkey/
touch "/var/log/security_monkey/security_monkey-deploy.log"
python manage.py db upgrade
