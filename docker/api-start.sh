#!/bin/bash

cd /usr/local/src/security_monkey
# export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-deploy.py
python manage.py run_api_server -b 0.0.0.0:5000
