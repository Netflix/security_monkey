#!/bin/bash
rm -rf /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey
rm -rf /var/lib/jenkins/jobs/security_monkey_build/workspace/*.deb
# mkdir -p /var/lib/jenkins/jobs/security_monkey_build/workspace/build
cd /var/lib/jenkins/jobs/security_monkey_build/workspace/
# virtualenv build
# source build/bin/activate
# . build/bin/activate
# cd build
git clone git@github.com:Symantec/security_monkey.git

# copy envs into the packaing dir
cp packaging/envs security_monkey/
# mkdir -p security_monkey/source
virtualenv security_monkey
. security_monkey/bin/activate
cd security_monkey
pip install -r requirements.txt
python setup.py install

cd /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey/dart
/usr/lib/dart/bin/pub get
/usr/lib/dart/bin/pub build
mkdir -p /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey/security_monkey/static/

/usr/local/bin/fpm -s dir -t deb -n security-monkey -v 0.41 --iteration 7 -d "python-psycopg2,postgresql,postgresql-contrib,libpq-dev,supervisor,libffi-dev,nginx" --after-install /var/lib/jenkins/jobs/security_monkey_build/workspace/packaging/long_post_install_new.sh /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey

# /usr/local/bin/fpm -s dir -t deb -n security-monkey -v 0.41 --iteration 1 -d "python-psycopg2,postgresql,postgresql-contrib,libpq-dev,supervisor,libffi-dev" /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey

mv *deb /var/lib/jenkins/jobs/security_monkey_build/workspace/security-monkey_0.41.7_all.deb