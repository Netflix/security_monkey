#!/bin/bash
# /usr/local/src/security_monkey/

# run this after sudo su -
# sudo apt-get update
# sudo apt-get -y install python-pip python-dev python-psycopg2 postgresql postgresql-contrib libpq-dev nginx supervisor git libffi-dev curl

#Create the logging folders

# sudo mkdir /var/log/security_monkey
# sudo chown www-data /var/log/security_monkey
# sudo mkdir /var/www
# sudo chown www-data /var/www
# sudo touch /var/log/security_monkey/security_monkey.error.log
# sudo touch /var/log/security_monkey/security_monkey.access.log
# sudo touch /var/log/security_monkey/security_monkey-deploy.log
# sudo chown www-data /var/log/security_monkey/security_monkey-deploy.log


rm -rf /usr/local/src/security_monkey/
cd /usr/local/src
git clone --depth 1 --branch master https://github.com/Netflix/security_monkey.git
virtualenv security_monkey
source /usr/local/src/security_monkey/bin/activate
cd security_monkey
pip install -r requirements.txt
python setup.py install

# download, compile and install web UI
curl https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
cd ~
curl https://storage.googleapis.com/download.dartlang.org/linux/debian/dart_stable.list > dart_stable.list
mv dart_stable.list /etc/apt/sources.list.d/dart_stable.list
apt-get update
apt-get install -y dart=1.12.2-1

# Build the Web UI
cd /usr/local/src/security_monkey/dart
#Should we use ENV or just naive structure?
/usr/lib/dart/bin/pub get
/usr/lib/dart/bin/pub build

# Copy the compiled Web UI to the appropriate destination
/bin/mkdir -p /usr/local/src/security_monkey/security_monkey/
wget https://github.com/Netflix/security_monkey/releases/download/v0.4.1/static.tar.gz
tar -zxvf static.tar.gz
# sudo /bin/cp -R /usr/local/src/security_monkey/dart/web/* /usr/local/src/security_monkey/security_monkey/static/

# copy supervisor configuration file
cp /usr/local/src/security_monkey/supervisor/security_monkey.conf /etc/supervisor/conf.d/security_monkey.conf
apt-get -y install ruby-dev gcc make
gem install fpm

cd ~
# sudo /usr/local/bin/fpm -s dir -t deb -n security_monkey -v 0.41 --iteration 1 -d python-pip -d python-dev -d python-psycopg2 -d postgresql -d postgresql-contrib -d libpq-dev -d nginx -d supervisor -d git -d libffi-dev -d libxml2 /usr/local/src/security_monkey/ /etc/supervisor/conf.d/ 
/usr/local/bin/fpm -s dir -t deb -n security_monkey -v 0.41 --iteration 1 -d python-pip -d python-dev -d python-psycopg2 -d postgresql -d postgresql-contrib -d libpq-dev -d nginx -d supervisor -d git -d libffi-dev -d libxml2 /usr/local/src/security_monkey/ /var/log/security_monkey /var/www

# remaining steps
# setup datastore, for demo and for now, setup postgres
# sudo -u postgres psql postgres
# \password postgres
# Enter new password: securitymonkeypassword
# Enter it again: securitymonkeypassword
# cd /usr/local/src/security_monkey/
# sudo -E python manage.py db upgrade
# export SECURITY_MONKEY_SETTINGS=/usr/local/src/security_monkey/env-config/config-deploy.py
# sudo -u postgres createdb secmonkey
# Edit /usr/local/src/security_monkey/env-config/config-deploy.py:
# Setting up Supervisor
# setup certificate
# setup nginx configuration (/etc/nginx/sites-available/securitymonkey.conf)