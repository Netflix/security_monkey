#!/bin/bash
rm -rf /var/lib/jenkins/jobs/security_monkey_build/workspace/build
mkdir -p /var/lib/jenkins/jobs/security_monkey_build/workspace/build
cd /var/lib/jenkins/jobs/security_monkey_build/workspace/
virtualenv build
source build/bin/activate
pip install -r requirements.txt
python setup.py install

cd /var/lib/jenkins/jobs/security_monkey_build/workspace/dart
/usr/lib/dart/bin/pub get
/usr/lib/dart/bin/pub build
mkdir -p /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey/static/
/bin/cp -R /var/lib/jenkins/jobs/security_monkey_build/workspace/dart/web/* /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey/static/
/usr/local/bin/fpm -s dir -t deb -n security_monkey -v 0.41 --iteration 1 -d python-pip -d python-dev -d python-psycopg2 -d postgresql -d postgresql-contrib -d libpq-dev -d nginx -d supervisor -d git -d libffi-dev -d libxml2 /var/lib/jenkins/jobs/security_monkey_build/workspace --after-install /var/lib/jenkins/jobs/security_monkey_build/workspace/packaging/post_install.sh
