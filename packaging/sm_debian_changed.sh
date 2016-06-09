#!/bin/bash
#rm -rf /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey
#rm -rf /var/lib/jenkins/jobs/security_monkey_build/workspace/*.deb
# mkdir -p /var/lib/jenkins/jobs/security_monkey_build/workspace/build
#cd /var/lib/jenkins/jobs/security_monkey_build/workspace/
# virtualenv build
# source build/bin/activate
# . build/bin/activate
# cd build
#git clone git@github.com:Symantec/security_monkey.git
#cd security_monkey
# copy envs into the packaing dir
cp packaging/envs security_monkey/
virtualenv security_monkey
. security_monkey/bin/activate
cd security_monkey
pip install -r requirements.txt
python setup.py install

#cd /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey/dart
/usr/lib/dart/bin/pub get
/usr/lib/dart/bin/pub build
#mkdir -p /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey/security_monkey/static/

fpm -s dir -t deb -n security-monkey -v 0.41 --iteration 12 -d "python-psycopg2,postgresql,postgresql-contrib,libpq-dev,supervisor,libffi-dev,nginx" --after-install packaging/long_post_install_new.sh /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey

mv *deb /var/lib/jenkins/jobs/security_monkey_build/workspace/security-monkey_0.41.12_all.deb
