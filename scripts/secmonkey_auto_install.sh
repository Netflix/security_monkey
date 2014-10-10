#!/bin/bash
################################################################################################
# Bash script to automate installation of Security Monkey.
#
# This script assumes that you're going to run Security Monkey on an Ubuntu EC2 Instance in AWS.
#
# This script will work for a Postgres DB installation on both RDS and localhost.
#
# I'm sure it could be significantly improved on and I'd love feedback on "how" :)
#
# Written by :: markofu
#
# Date :: September 2014
#
# Version History :: 
#
#       0.1 :: September 2014 :: First version submitted to Netflix Develop Branch. Few issues.
#       0.2 :: October 2014   :: Fixed a few aesthetics
#
# To Do :: 
#         Clean up redundant keys
#         Remove requirement to enter password for Postgres
#         Improve Docs?
#         Improve as per feedback
#         Fix bug with password containing !
################################################################################################
 
set -e 

### Declaring some variables

USAGE="Usage: $(basename $0) [-hv] [-d arg] [-e arg] [-i arg] [-n arg] [-p arg] [-r arg] [-s arg] [-u arg] [-w arg].

For example - 

              bash $(basename $0) -d 10.11.1.11 -e cert_email@secmonkey.com -i 10.10.10.10 -n ec2-10-10-10-10.us-west-1.compute.amazonaws.com -p SuperSecretPasswordYo -r recipient@secmonkey.com -s sender@secmonkey.com -u postgres -w secmonkey.com
    
              bash $(basename $0) -h 

              bash $(basename $0) -v
    

CLI switches - 
              -d  >> Hostname or IP Address of the Postgres Database
              -e  >> Email Address used for SSL Cert for the Security Monkey Instance
              -i  >> IP Address (what you want the hostname resolve to) of the SecurityMonkey Instance
              -h  >> Prints this message
              -n  >> Hostname of the SecurityMonkey Instance
              -p  >> Password for the Postgres DB on the SecurityMonkey Instance
              -r  >> Recipient Email Address for the Security Monkey Notifications
              -s  >> Sender Email Address for the Security Monkey Notifications
              -u  >> Postgres DB User
              -v  >> Version of the $(basename $0)
              -w  >> Site (Domain) be used for the self-signed certificate
    "

VERSION="0.2"
ARGS=$#

err_code=10
f_hosts="/etc/hosts"
f_hostname="/etc/hostname"
f_lsb="/etc/lsb-release"
f_debug="/var/tmp/sec_monkey_install_debug.log"
f_nginx_site_a="/etc/nginx/sites-available/securitymonkey.conf"
f_nginx_site_e="/etc/nginx/sites-enabled/securitymonkey.conf"
f_nginx_default="/etc/nginx/sites-enabled/default"

### Function to check that the script is being run with options.

check_opt ()
{
    if [ $ARGS -eq 0 ]
    then
        echo -e "\nPlease run with valid options! Help is printed with '-h'.\n"
        echo -e "\n$USAGE\n"
        ($err_code++) && exit $(expr $err_code - 1) 
    elif [ $ARGS -gt 20 ]
    then
        echo -e "\nPlease examine the usage options for this script - you can only have a maximum of 7 command line switches!\n" && echo -e "\n$USAGE\n"
        ($err_code++) && exit $(expr $err_code - 1) 
    fi
}

### Function to check that the script only runs with appropriate options when looking for help or version

check_opt_one ()
{
    if [ $ARGS -gt 2 ]
    then 
        echo -e "\nPlease run with only one option! Help is printed with '-h'.\n"
        echo -e "\n$USAGE\n"
        ($err_code++) && exit $(expr $err_code - 1) 
    fi
}

### Parsing cli options

parse_arg ()
{
    for arg in "$@"
    do
        case $arg in
             -d|--database) # Hostname or IP Address of the Postgres Database
                 db=$2
                 shift 2
                 ;;
             -e|--email) # Email Address used for SSL Cert for the Security Monkey Instance
                 email=$2
                 shift 2
                 ;;
             -h|--help)
                 check_opt_one
                 echo -e "\n$USAGE\n"
                 exit 0;
                 ;;
             -i|--ip) # IP Address of the SecurityMonkey Instance
                 real_ip=$2
                 shift 2
                 ;;
             -n|--name) # Hostname of the SecurityMonkey Instance
                 name=$2
                 shift 2
                 ;;
             -p|--password) # Password for the Postgres DB on the SecurityMonkey Instance
                 password=$2
                 shift 2
                 ;;
             -r|--recipient) # Recipient Email Address that receives Security Monkey Notifications
                 recipient=$2
                 shift 2
                 ;;
             -s|--sender) # Sender Email Address for the Security Monkey Notifications
                 sender=$2
                 shift 2
                 ;;
             -u|--user) # Postgres DB User
                 user=$2
                 shift 2
                 ;;
             -v|--version)
                 check_opt_one
                 echo -e "\nVersion $VERSION.\n"
                 exit 0;
                 ;;
             -w|--website) # Site (Domain) be used for the self-signed certificate
                 website=$2
                 shift 2
                 ;;
        esac
    done
}

### Function set locales as it's typically screwed up in Ubuntu on AWS after inital install

fix_locales ()
{
	export LANGUAGE=en_US.UTF-8
	export LANG=en_US.UTF-8
	export LC_ALL=en_US.UTF-8
	locale-gen en_US.UTF-8
	sudo dpkg-reconfigure locales
}

### Fuction to Clear Bash History

clear_hist ()
{
    cat /dev/null > ~/.bash_history && history -c
}

### Function to Create Static Variables

create_static_var ()
{
    dir_net="/var/tmp/net" 					# This script is typically copied up to /var/tmp and the net tarball is untarred there
    dir_sm="/apps/security_monkey"
    dir_config="$dir_sm/env-config"  				# Config Directory in Security Monkey
    dir_super="$dir_sm/supervisor"  				# Supervisor Directory in Security Monkey
    dir_nginx_log="/var/log/nginx/log"
    dir_ssl="/etc/ssl"
    file_deploy="$dir_config/config-deploy.py"
    file_ini="$dir_super/security_monkey.ini"
    file_rc="$HOME/.bashrc"

    if [ -d $dir_sm ]
    then
        echo -e "\n$dir_sm already exists\n" > $f_debug
    else
        sudo mkdir -p $dir_sm
    fi
    
    export SECURITY_MONKEY_SETTINGS="$file_deploy"		# SECURITY_MONKEY_SETTINGS variable should point to the config-deploy.py file
    exec "$@"

    if grep -Fq "export SECURITY_MONKEY_SETTINGS=" $file_rc
    then
        echo -e "\nEnv Variable SECURITY_MONKEY_SETTINGS already exists in $file_rc\n" >> $f_debug
    else
        echo -e "\n# Security Monkey Settings\nexport SECURITY_MONKEY_SETTINGS=\"$file_deploy\"\n" | sudo tee -ai $file_rc # Adding to the local .bashrc file
    fi
    . ~/.bashrc
}

#### Function Definitions Start ###

check_ubuntu ()
{
    if grep -Fxq DISTRIB_ID=Ubuntu $f_lsb
    then
        echo -e "\nYou're running Ubuntu, gg :)\n" >> $f_debug
    else
        echo -e "\nYou don't seem to be running a Ubuntu distro, sorry :( Please only run this on Ubuntu! Now exiting.....\n" && ($err_code++) && exit $(expr $err_code - 1)
    fi
}

### Hostnname
create_host ()
{
	echo -e "\nThis Security Monkey instance has a real ip of $real_ip and a hostname of $name....\n"
	# Checking if the IP of the Security Monkey Instance is in Hosts file
    if grep -Fq $real_ip $f_hosts
    then
        echo -e "\n$real_ip is in the $f_hosts file already, moving on.....\n" >> $f_debug
    else
        echo -e "\n$real_ip	$name\n" | sudo tee -ai $f_hosts >> $f_debug
    fi

    sudo hostname $name # Just ensuring that the hostname is correctly set as per the cli prior to install

	# Checking if the hostname of the Security Monkey Instance is in Hostname file
    if grep -Fqi $name $f_hostname
    then
        echo -e "\nHostname for $real_ip is $name and is in $f_hostname.\n" >> $f_debug
    else
        sudo sed -i.bak -e's/ip.*/\$name/i' $f_hostname
    fi
}

### Install pre-reqs

install_post ()
{
    echo -e "\nInstalling Postgres on the localhost so must NOT be using a RDS, let's hope so.....\n"
    sudo apt-get install -y postgresql postgresql-contrib 
}

install_pre ()
{
    sudo apt-get update && sudo apt-get install -y python-pip python-dev python-psycopg2 libpq-dev nginx supervisor git postgresql-client
    if (($db)) # Checking if the $db variable is an arithmetic operator
    then
        [[ $db =~ 127.0.0.1 ]] && install_post
    elif [[ $db -eq localhost ]]
    then
        install_post
    else
       echo -e "\nNot installing Postgres on the localhost so must be using a RDS, let's hope so.....\n"
    fi
}

# Connect to the 'postgres' db (assumed to be your default db)
# Modify user password and create secmonkey db
create_db ()
{
    echo -e "We will now create a Postgres DB user as per your CLI options and you will be prompted for the password....\n"
    sleep 3
    echo -e "\nWe will now create the _secmonkey_ DB user as per your CLI options and you will be re-prompted for the password....\n"
    psql -U $user -d postgres -h $db -c "alter user $user with password '$password';"
    psql -U $user -h $db -d postgres -c 'CREATE DATABASE secmonkey'
}

# The following functions are used to create the security_monkey.ini and config_deploy.py files respectively.
# They are called subsequently by various db scripts

create_ini_file ()
{
    sudo rm $file_ini

cat << EOF | sudo tee -ai $file_ini
[unix_http_server]
file=/tmp/supervisor.sock;

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock;

[rpcinterface:supervisor]
supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface

[supervisord]
logfile=/tmp/securitymonkey.log
logfile_maxbytes=50MB
logfile_backups=2
loglevel=trace
pidfile=/tmp/supervisord.pid
nodaemon=false
minfds=1024
minprocs=200
user=ubuntu

[program:securitymonkey]
command=python $dir_sm/manage.py run_api_server
environment=SECURITY_MONKEY_SETTINGS="$file_deploy"

[program:securitymonkeyscheduler]
command=python $dir_sm/manage.py start_scheduler

directory=$dir_sm
environment=PYTHONPATH='$dir_sm/',SECURITY_MONKEY_SETTINGS="$file_deploy"
user=ubuntu
autostart=true
autorestart=true
EOF

}

create_config_file ()
{
    sudo rm $file_deploy

cat << EOF | sudo tee -ai $file_deploy
# Insert any config items here.
# This will be fed into Flask/SQLAlchemy inside security_monkey/__init__.py

LOG_LEVEL = "DEBUG"
LOG_FILE = "security_monkey-deploy.log"

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:$password@$db:5432/secmonkey'

SQLALCHEMY_POOL_SIZE = 50
SQLALCHEMY_MAX_OVERFLOW = 15
ENVIRONMENT = 'ec2'
USE_ROUTE53 = False
FQDN = '$name'
API_PORT = '5000'
WEB_PORT = '443'
FRONTED_BY_NGINX = True
NGINX_PORT = '443'
WEB_PATH = '/static/ui.html'

SECRET_KEY = 'O3GYKSrqey5SeDhnbcvBNNKl'

DEFAULT_MAIL_SENDER = '$sender'
SECURITY_REGISTERABLE = True
SECURITY_CONFIRMABLE = False
SECURITY_RECOVERABLE = False
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = 'gnoSLMMnUIlk2iLhDkW7OgFZ'
SECURITY_POST_LOGIN_VIEW = 'https://$name'

# This address gets all change notifications
SECURITY_TEAM_EMAIL = '$recipient'
EOF

}

### Cloning the SecurityMonkey repo from Github & Installs SecurityMonkey

clone_install ()
{
    sudo git clone https://github.com/Netflix/security_monkey.git $dir_sm
    sudo chown -R ubuntu:ubuntu $dir_sm
    cd $dir_sm && sudo python setup.py install

    create_config_file
    
    sudo -E python $dir_sm/manage.py db upgrade 			# Need to keep local environment variables when sudo to python because we need to know where SECURITY_HOME_SETTINGS is. Hence, "-E".
    clear_hist
}

### Automating the creation of the self-signed certificate

create_ss_cert ()
{
    if [ -z "$website" ]
    then
        echo -e "\n$USAGE\n"
  	    ($err_code++) && exit $(expr $err_code - 1)
  	fi

# Generate a passphrase
PASSPHRASE=$(head -c 500 /dev/urandom | tr -dc a-z0-9A-Z | head -c 128; echo)

# Certificate details; replace items in angle brackets with your own info
subj="
C=US
ST=OR
O=Riot Games
localityName=PO
commonName=$website
organizationalUnitName=InfoSec
emailAddress=$email
"

# Generate the server private key
echo -e "\nGenerating the server private key.....\n"
sudo openssl genrsa -des3 -out $website.key -passout pass:$PASSPHRASE 2048
echo $PASSPHRASE
# Generate the CSR
echo -e "\nGenerating the CSR.....\n"
sudo openssl req \
    -new \
    -batch \
    -subj "$(echo -n "$subj" | tr "\n" "/")" \
    -key $website.key \
    -out $website.csr \
    -passin pass:$PASSPHRASE

cp $website.key $website.key.org

# Strip the password so we don't have to type it every time we restart nginx
echo -e "\nStriping the password from the site key.....\n"
sudo openssl rsa -in $website.key.org -out $dir_ssl/private/server.key -passin pass:$PASSPHRASE

# Generate the cert (good for 3 years)
echo -e "\nGenerating the 3-year cert...\n"
sudo openssl x509 -req -days 1095 -in $website.csr -signkey $dir_ssl/private/server.key -out $dir_ssl/certs/server.crt
}

### this function configures .ini file & starts the supervisor process

cs_supervisor ()
{
    create_ini_file

    sudo -E supervisord -c $file_ini

    echo -e "\n The next command 'supervisorctl' command will leave you in the 'supervisor' prompt, simply type 'quit' to exit and complete the Security Monkey install....\n" && sleep 3
    sudo -E supervisorctl -c $file_ini
}

### This function configures nginx
config_nginx ()
{
    sudo mkdir -p $dir_nginx_log
    sudo touch $dir_nginx_log/securitymonkey.access.log
    sudo touch $dir_nginx_log/securitymonkey.error.log

    [[ -s $f_nginx_site_a ]] && sudo cp $f_nginx_site_a $f_nginx_site_a.$(date +%Y-%m-%d) && sudo rm $f_nginx_site_a

cat << EOF | sudo tee -ai $f_nginx_site_a
server {
   listen      0.0.0.0:443 ssl;
   ssl_certificate /etc/ssl/certs/server.crt;
   ssl_certificate_key /etc/ssl/private/server.key;
   access_log  /var/log/nginx/log/securitymonkey.access.log;
   error_log   /var/log/nginx/log/securitymonkey.error.log;

    location /register {
        proxy_read_timeout 120;
        proxy_pass  http://127.0.0.1:5000;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_redirect off;
        proxy_buffering off;
        proxy_set_header        Host            \$host;
        proxy_set_header        X-Real-IP       \$remote_addr;
        proxy_set_header        X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /logout {
        proxy_read_timeout 120;
        proxy_pass  http://127.0.0.1:5000;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_redirect off;
        proxy_buffering off;
        proxy_set_header        Host            \$host;
        proxy_set_header        X-Real-IP       \$remote_addr;
        proxy_set_header        X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /login {
        proxy_read_timeout 120;
        proxy_pass  http://127.0.0.1:5000;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_redirect off;
        proxy_buffering off;
        proxy_set_header        Host            \$host;
        proxy_set_header        X-Real-IP       \$remote_addr;
        proxy_set_header        X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /api {
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
        root /apps/security_monkey/security_monkey/static;
        index ui.html;
    }

    location / {
        root /apps/security_monkey/security_monkey/static;
        index ui.html;
    }

}
EOF

    [[ ! -e $f_nginx_site_e ]] && sudo ln -s $f_nginx_site_a $f_nginx_site_e # Symlink the available site to the enabled site
    [[ -e $f_nginx_default ]] && sudo rm $f_nginx_default # removing the default site
    sudo service nginx restart
    clear_hist
}

### Main :: Running the functions ###

check_opt $@

parse_arg $@

check_ubuntu

fix_locales

create_host

create_static_var

install_pre

create_db

clone_install

cs_supervisor

create_ss_cert

config_nginx
