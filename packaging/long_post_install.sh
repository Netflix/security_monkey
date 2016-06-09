#!/bin/bash
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
#  mv -v /var/lib/jenkins/jobs/security_monkey_build/workspace/* /var/lib/jenkins/jobs/security_monkey_build/security_monkey
ln -s /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey /usr/local/src/security_monkey

# cp -r /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey  /usr/local/src
# cp /usr/local/src/security_monkey/supervisor/security_monkey.conf /etc/supervisor/conf.d/security_monkey.conf
cp -R /usr/local/src/security_monkey/dart/build/web/* /usr/local/src/security_monkey/security_monkey/static/
# sudo rm -rf /var/lib/jenkins/
# ln -s /var/lib/jenkins/jobs/security_monkey_build/workspace/security_monkey /usr/local/src/security_monkey
# sudo apt-get -f install
# sudo apt-get -y install python-psycopg2 postgresql postgresql-contrib libpq-dev supervisor libffi-dev
cp /usr/local/src/security_monkey/supervisor/security_monkey.conf /etc/supervisor/conf.d/security_monkey.conf

# DEBIAN_FILE1=$1
# dpkg -i $DEBIAN_FILE1
# apt-get update
# apt-get install -fy 

# setup logging
sm_log=/var/log/security_monkey

if [ ! -d "$sm_log" ]; then
    mkdir $sm_log
fi

www=/var/www

if [ ! -d "$www" ]; then
    mkdir $www
fi

# sudo mkdir /var/log/security_monkey
sudo chown www-data /var/log/security_monkey
# sudo mkdir /var/www
sudo chown www-data /var/www

err_log=/var/log/security_monkey/security_monkey.error.log
access_log=/var/log/security_monkey/security_monkey.access.log
deploy_log=/var/log/security_monkey/security_monkey.error.log

if [ ! -e "$err_log" ]; then
    touch $err_log
fi

if [ ! -e "$access_log" ]; then
    touch $access_log
fi

if [ ! -e "$deploy_log" ]; then
    touch $deploy_log
fi

# sudo touch /var/log/security_monkey/security_monkey.access.log
# sudo touch /var/log/security_monkey/security_monkey-deploy.log

sudo chown www-data /var/log/security_monkey/security_monkey-deploy.log

export SECURITY_MONKEY_SETTINGS=/usr/local/src/security_monkey/env-config/config-deploy.py
export PUBLIC_IP='172.16.152.171'
export SECRET_KEY='securityMonkeySecrete'
export SALT='securityMonkeySalt'
export PASS='1234'
export SECPASS='securitymonkeypassword'

#configure application
sudo sed -i.bak 's@ec2-XX-XXX-XXX-XXX.compute-1.amazonaws.com@'"$PUBLIC_IP"'@' /usr/local/src/security_monkey/env-config/config-deploy.py
sudo sed -i.bak "s/SECRET_KEY = '<INSERT_RANDOM_STRING_HERE>'/SECRET_KEY = '$SECRET_KEY'/g" /usr/local/src/security_monkey/env-config/config-deploy.py
sudo sed -i.bak "s/SECURITY_PASSWORD_SALT = '<INSERT_RANDOM_STRING_HERE>'/SECURITY_PASSWORD_SALT = '$SALT'/g" /usr/local/src/security_monkey/env-config/config-deploy.py

# setup postgres user password
# sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'securitymonkeypassword';"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD $SECPASS;"

# if ! psql -lqt | cut -d \| -f 1 | grep -w secmonkey; then
sudo -u postgres createdb secmonkey
# fi

# if ! [psql -lqt | cut -d \| -f 1 | grep -w secmonkey]; then
    
# configure nginx
# whoami
sudo bash -c 'cat <<EOF > /etc/nginx/sites-available/securitymonkey.conf

add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header X-Frame-Options "SAMEORIGIN";
add_header Strict-Transport-Security "max-age=631138519";
add_header Content-Security-Policy "default-src 'self'; font-src 'self' https://fonts.gstatic.com; script-src 'self' https://ajax.googleapis.com; style-src 'self' https://fonts.googleapis.com;";

server {
   listen      0.0.0.0:443 ssl;
   ssl_certificate /etc/ssl/certs/server.crt;
   ssl_certificate_key /etc/ssl/private/server.key;
   access_log  /var/log/security_monkey/security_monkey.access.log;
   error_log   /var/log/security_monkey/security_monkey.error.log;

   location ~* ^/(reset|confirm|healthcheck|register|login|logout|api) {
        proxy_read_timeout 120;
        proxy_pass  http://127.0.0.1:5000;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_redirect off;
        proxy_buffering off;
        proxy_set_header        Host            \$host;
        proxy_set_header        X-Real-IP       \$remote_addr;
        proxy_set_header        X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /static {
        rewrite ^/static/(.*)$ /$1 break;
        root /usr/local/src/security_monkey/security_monkey/static;
        index ui.html;
    }

    location / {
        root /usr/local/src/security_monkey/security_monkey/static;
        index ui.html;
    }

}

EOF'

cd /usr/local/src/security_monkey/ 
# sudo -E python manage.py db upgrade
sudo -E /usr/local/src/security_monkey/bin/python manage.py db upgrade
sudo cp supervisor/security_monkey.conf /etc/supervisor/conf.d/security_monkey.conf
sudo service supervisor restart
sudo supervisorctl restart securitymonkeyscheduler
sudo supervisorctl restart securitymonkey
sudo rm -rf "/etc/nginx/sites-enabled/default"

# setup certificate 

# openssl genrsa -des3 -out server.key -passout pass:1234 2048 -subj “/C=US/ST=Oregon/L=Portland/O=IT/CN=www.example.com”
openssl genrsa -des3 -out server.key -passout pass:$PASS 2048 -subj “/C=US/ST=Oregon/L=Portland/O=IT/CN=www.example.com”

# openssl rsa -in server.key -out server.key.insecure -passin pass:1234
openssl rsa -in server.key -out server.key.insecure -passin pass:$PASS

mv server.key server.key.secure
mv server.key.insecure server.key

# openssl req -new -key server.key -out server.csr -subj "/C=US/ST=Oregon/L=Portland/O=IT/CN=www.example.com" -passin pass:1234
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=Oregon/L=Portland/O=IT/CN=www.example.com" -passin pass:$PASS

# openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt -passin pass:1234
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt -passin pass:$PASS
sudo cp server.crt /etc/ssl/certs
sudo cp server.key /etc/ssl/private
sudo ln -s /etc/nginx/sites-available/securitymonkey.conf /etc/nginx/sites-enabled/securitymonkey.conf
sudo service nginx restart
