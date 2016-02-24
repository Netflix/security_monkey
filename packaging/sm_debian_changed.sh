#!/bin/bash
rm -rf /var/lib/jenkins/jobs/security_monkey_build/workspace/build
mkdir -p /var/lib/jenkins/jobs/security_monkey_build/workspace/build
cd /var/lib/jenkins/jobs/security_monkey_build/workspace/
virtualenv build
source build/bin/activate
cd build
git clone git@github.com:Symantec/security_monkey.git
cd security_monkey
# pip install -r requirements.txt
# python setup.py install

cd /var/lib/jenkins/jobs/security_monkey_build/workspace/build/security_monkey/dart
/usr/lib/dart/bin/pub get
/usr/lib/dart/bin/pub build
mkdir -p /var/lib/jenkins/jobs/security_monkey_build/workspace/build/security_monkey/security_monkey/static/
# /bin/cp -R /var/lib/jenkins/jobs/security_monkey_build/workspace/dart/web/* /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey/static/
/usr/local/bin/fpm -s dir -t deb -n security_monkey -v 0.41 --iteration 1 -d python-pip -d python-dev -d python-psycopg2 -d postgresql -d postgresql-contrib -d libpq-dev -d nginx -d supervisor -d git -d libffi-dev -d libxml2 --after-install /var/lib/jenkins/jobs/security_monkey_build/workspace/packaging/post_install.sh /var/lib/jenkins/jobs/security_monkey_build/workspace/build
mv *deb /var/lib/jenkins/jobs/security_monkey_build/workspace/securitymonkey_0.41.1_all.deb

# cloudfire-core-mib_0.117.1_all.deb