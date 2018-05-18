#!/bin/bash

# wait for the scheduler
sleep 20

mkdir -p /var/log/security_monkey
touch /var/log/security_monkey/security_monkey-deploy.log

cd /usr/local/src/security_monkey
celery -A celery -A security_monkey.task_scheduler.tasks.CELERY worker -E
