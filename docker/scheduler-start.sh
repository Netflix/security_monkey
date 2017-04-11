#!/bin/bash

# wait the database
sleep 10

mkdir -p /var/log/security_monkey
touch /var/log/security_monkey/security_monkey-deploy.log

cd /usr/local/src/security_monkey
python manage.py start_scheduler
