#!/bin/bash

mkdir -p /var/log/security_monkey
touch /var/log/security_monkey/security_monkey-deploy.log

cd /usr/local/src/security_monkey
# export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-deploy.py
python manage.py start_scheduler
