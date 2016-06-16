#!/bin/bash
# Log setup
sudo mkdir /var/log/security_monkey
sudo chown www-data /var/log/security_monkey
sudo mkdir /var/www
sudo chown www-data /var/www
sudo touch /var/log/security_monkey/security_monkey.error.log
sudo touch /var/log/security_monkey/security_monkey.access.log
sudo touch /var/log/security_monkey/security_monkey-deploy.log
sudo chown www-data /var/log/security_monkey/security_monkey-deploy.log
sudo mkdir -p /usr/local/src/
sudo mkdir -p /var/lib/jenkins/jobs/security_monkey_build/security_monkey/
# ln -s /security_monkey /usr/local/src/security_monkey
ln -s / /usr/local/src/security_monkey
wget https://github.com/Netflix/security_monkey/releases/download/v0.4.1/static.tar.gz
tar -zxvf static.tar.gz
cp -R static /usr/local/src/security_monkey/security_monkey
# cp -R /usr/local/src/security_monkey/dart/build/web/* /usr/local/src/security_monkey/security_monkey/static/
cp /usr/local/src/security_monkey/supervisor/security_monkey.conf /etc/supervisor/conf.d/security_monkey.conf
sm_log=/var/log/security_monkey

if [ ! -d "$sm_log" ]; then
    mkdir $sm_log
fi

www=/var/www

if [ ! -d "$www" ]; then
    mkdir $www
fi

sudo chown www-data /var/log/security_monkey
sudo chown www-data /var/www

err_log=/var/log/security_monkey/security_monkey.error.log
access_log=/var/log/security_monkey/security_monkey.access.log
deploy_log=/var/log/security_monkey/security_monkey.error.log
# envs=/var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey/envs
envs=/env
if [ ! -e "$err_log" ]; then
    touch $err_log
fi

if [ ! -e "$access_log" ]; then
    touch $access_log
fi

if [ ! -e "$deploy_log" ]; then
    touch $deploy_log
fi

sudo chown www-data /var/log/security_monkey/security_monkey-deploy.log

# setup environment variables
export SECURITY_MONKEY_SETTINGS=/usr/local/src/security_monkey/env-config/config-deploy.py
export PUBLIC_IP=$(cat $envs | grep "PUBLIC_IP" | sed 's/.*=//')
export SECRET_KEY=$(cat $envs | grep "SECRET_KEY" | sed 's/.*=//')
export SALT=$(cat $envs | grep "SALT" | sed 's/.*=//')
export DB_URI=$(cat $envs | grep "SQLALCHEMY_DATABASE_URI" | sed 's/.*=//')

# configure application
sudo sed -i.bak 's@ec2-XX-XXX-XXX-XXX.compute-1.amazonaws.com@'"$PUBLIC_IP"'@' /usr/local/src/security_monkey/env-config/config-deploy.py
sudo sed -i.bak "s/SECRET_KEY = '<INSERT_RANDOM_STRING_HERE>'/SECRET_KEY = '$SECRET_KEY'/g" /usr/local/src/security_monkey/env-config/config-deploy.py
sudo sed -i.bak "s/SECURITY_PASSWORD_SALT = '<INSERT_RANDOM_STRING_HERE>'/SECURITY_PASSWORD_SALT = '$SALT'/g" /usr/local/src/security_monkey/env-config/config-deploy.py
sudo sed -i.bak "s/SQLALCHEMY_DATABASE_URI = '<INSERT_DB_CONNECTION_HERE>'/SQLALCHEMY_DATABASE_URI = '$DB_URI'/g" /usr/local/src/security_monkey/env-config/config-deploy.py

# upgrade DB schema and supervisor
cd /usr/local/src/security_monkey/ 
sudo -E /usr/local/src/security_monkey/security_monkey/bin/python manage.py db upgrade
sudo cp supervisor/security_monkey.conf /etc/supervisor/conf.d/security_monkey.conf
sudo service supervisor restart
sudo supervisorctl restart securitymonkeyscheduler
sudo supervisorctl restart securitymonkey

# setup certificate: this is only for internal cert which will let 443 to be listening, which will further trigger health check
# an external cert will also be setup through spinnaker
openssl genrsa -des3 -out server.key -passout pass:1234 2048 -subj “/C=US/ST=Oregon/L=Portland/O=IT/CN=www.example.com”
openssl rsa -in server.key -out server.key.insecure -passin pass:1234
mv server.key server.key.secure
mv server.key.insecure server.key
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=Oregon/L=Portland/O=IT/CN=www.example.com" -passin pass:1234
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt -passin pass:1234
sudo cp server.crt /etc/ssl/certs
sudo cp server.key /etc/ssl/private

sudo ln -s /etc/apache2/mods-available/ssl.load  /etc/apache2/mods-enabled/ssl.load
sudo ln -s /etc/apache2/mods-available/proxy.load /etc/apache2/mods-enabled/proxy.load
sudo ln -s /etc/apache2/mods-available/headers.load /etc/apache2/mods-enabled/headers.load
sudo ln -s /etc/apache2/mods-available/proxy_http.load /etc/apache2/mods-enabled/proxy_http.load
sudo ln -s /etc/apache2/mods-available/rewrite.load /etc/apache2/mods-enabled/rewrite.load
sudo ln -s /usr/local/src/security_monkey/security_monkey/static/ui.html /usr/local/src/security_monkey/security_monkey/static/index.html


sudo bash -c 'cat <<EOF > /etc/apache2/sites-enabled/000-default.conf

<VirtualHost *:80>
  ServerName securitymonkey.symcpe.net
  Redirect permanent / https://securitymonkey.symcpe.net/
</VirtualHost>

<VirtualHost _default_:443>
  DocumentRoot /usr/local/src/security_monkey/security_monkey/static
  ServerName securitymonkey.symcpe.net:443

  Header add X-Content-Type-Options "nosniff"
  Header add X-XSS-Protection "1; mode=block"
  Header add X-Frame-Options "SAMEORIGIN"
  Header add Strict-Transport-Security "max-age=631138519"

  Options +FollowSymLinks -MultiViews
  RewriteEngine On
  RewriteRule ^/static/(.*)$ /\$1

  LogLevel warn
  SSLEngine on
  SSLProtocol all -SSLv2 -SSLv3 +TLSv1.2 +TLSv1.1 +TLSv1
  SSLHonorCipherOrder On
  SSLCipherSuite ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:DHE-RSA-AES128-SHA256:DHE-DSS-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:DHE-RSA-AES128-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK
  SSLCertificateFile /etc/ssl/certs/server.crt
  SSLCertificateKeyFile /etc/ssl/private/server.key


  ProxyPass "/api" "http://127.0.0.1:5000/api"
  ProxyPass "/reset" "http://127.0.0.1:5000/reset"
  ProxyPass "/confirm" "http://127.0.0.1:5000/confirm"
  ProxyPass "/healthcheck" "http://127.0.0.1:5000/healthcheck"
  ProxyPass "/register" "http://127.0.0.1:5000/register"
  ProxyPass "/login" "http://127.0.0.1:5000/login"
  ProxyPass "/logout" "http://127.0.0.1:5000/logout"


  <Directory "/usr/local/src/security_monkey/security_monkey/static">
    Require all granted
  </Directory>
</VirtualHost>
EOF'

sudo service apache2 restart
