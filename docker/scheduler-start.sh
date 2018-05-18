#!/bin/bash

# wait the database
sleep 10

mkdir -p /var/log/security_monkey
touch /var/log/security_monkey/security_monkey-deploy.log

cd /usr/local/src/security_monkey

echo "Starting Migrations"
monkey db upgrade
echo "Migrations Complete"

celery -A security_monkey.task_scheduler.beat.CELERY beat -l debug
