#!/bin/bash
# sudo mkdir /var/log/security_monkey
sudo chown www-data /var/log/security_monkey
# sudo mkdir /var/www
sudo chown www-data /var/www
sudo touch /var/log/security_monkey/security_monkey.error.log
sudo touch /var/log/security_monkey/security_monkey.access.log
sudo touch /var/log/security_monkey/security_monkey-deploy.log
sudo chown www-data /var/log/security_monkey/security_monkey-deploy.log
sudo mkdir -p /usr/local/src/
sudo mkdir -p /var/lib/jenkins/jobs/security_monkey_build/security_monkey/
# mv -v /var/lib/jenkins/jobs/security_monkey_build/workspace/* /var/lib/jenkins/jobs/security_monkey_build/security_monkey/
cp -r /var/lib/jenkins/jobs/security_monkey_build/workspace/build/security_monkey  /usr/local/src
cp /usr/local/src/security_monkey/supervisor/security_monkey.conf /etc/supervisor/conf.d/security_monkey.conf
cp -R /usr/local/src/security_monkey/dart/build/web/* /usr/local/src/security_monkey/security_monkey/static/
sudo rm -rf /var/lib/jenkins/