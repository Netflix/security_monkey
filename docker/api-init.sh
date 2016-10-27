#!/bin/bash

sudo -u postgres psql -h postgres --command "ALTER USER postgres with PASSWORD 'securitymonkeypassword';"
sudo -u postgres createdb -h postgres -O postgres secmonkey

mkdir -p /var/log/security_monkey/
touch "/var/log/security_monkey/security_monkey-deploy.log"

cd /usr/local/src/security_monkey
python manage.py db upgrade
