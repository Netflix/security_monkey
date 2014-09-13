#!/bin/bash
################################################################
# Bash script to automate installation of Security Monkey
#
# Should work for DB installation on RDS and localhost
# Written by :: markofu
#
# Version :: 0.1
#
# Date :: September 2014
#
################################################################
 
set -e 

### Declaring some variables

USAGE="Usage: $(basename $0) [-hv] [-d arg] [-i arg] [-n arg] [-p arg] [-s arg] [-u arg].
    For example - bash sm_install.sh -d 10.11.1.11 -e cert-email@secmonkey.com -i 10.10.10.10 -n ec2-10-10-10-10.us-west-1.compute.amazonaws.com -p SuperSecretPasswordYo -r recipient@secmonkey.com -s sender@secmonkey.com -u db_user -w secmonkey.com"

VERSION="0.1"
ARGS=$#

f_hosts="/etc/hosts"
f_hostname="/etc/hostname"
f_lsb="/etc/lsb-release"
f_debug="/var/tmp/sec_monkey_install_debug.log"


### Function to check that the script is being run with options.

check_opt ()
{
    if [ $ARGS -eq 0 ];
    then
        echo -e "$USAGE\n";
        echo -e "Please run with a valid option! Help is printed with '-h'."
        exit 11;
    elif [ $ARGS -gt 20 ];
    then
        echo -e "Please examine the usage options for this script - you can only have a maximum of 7 command line switches!\n" && echo -e "\n$USAGE\n";
        exit 12;
    else
    	echo -e "\nConfused....\n"
        exit 13;
    fi
}

### Parsing cli options

parse_arg ()
{
    for arg in "$@"
    do
        case $arg in
             -d|--database) # IP Address of the Postgres Database
                 db=$2
                 shift 2
                 ;;
             -e|--email) # Email Address used for SSL Cert for the Security Monkey Instance
                 email=$2
                 shift 2
                 ;;
             -i|--ip) # IP Address of the SecurityMonkey Instance
                 pub_ip=$2
                 shift 2
                 ;;
             -h|--help)
                 echo -e "\n$USAGE\n";
                 exit 0;
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
                 db_user=$2
                 shift 2
                 ;;
             -v|--version)
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
    file_deploy="$dir_config/config-deploy.py"
    file_ini="$dir_super/security_monkey.ini"
    file_rc="$HOME/.bashrc"

    if [ -d $dir_sm ];
    then
        sudo mkdir -p $dir_sm
    else
        echo -e "\n$dir_sm already exists\n" > $f_debug;
    fi
    
    export SECURITY_MONKEY_SETTINGS="$file_deploy"		# SECURITY_MONKEY_SETTINGS variable should point to the config-deploy.py file
    exec "$@"

    if grep -Fq "export SECURITY_MONKEY_SETTINGS=" $file_rc;
    then
        echo -e "\nEnv Variable SECURITY_MONKEY_SETTINGS already exists in $file_rc\n" >> $f_debug;
    else
        echo -e "\n# Security Monkey Settings\nexport SECURITY_MONKEY_SETTINGS=$file_deploy\n" | sudo tee -ai $file_rc; # Adding to the local .bashrc file
    fi
    . ~/.bashrc
}

#### Function Definitions Start ###

check_ubuntu ()
{
    if grep -Fxq DISTRIB_ID=Ubuntu $f_lsb;
    then
        echo -e "\nYou're running Ubuntu, gg :)\n"; >> $f_debug;
    else
        echo -e "\nYou don't seem to be running a Ubuntu distro, sorry :( Please only run this on Ubuntu! Now exiting.....\n" && exit 14;
    fi
}

### Hostnname
create_host ()
{
	# Checking if the IP of the Security Monkey Instance is in Hosts file
    if grep -Fq $pub_ip $f_hosts;
    then
        echo -e "\n$pub_ip is in the $f_hosts file already, moving on.....\n" >> $f_debug;
    else
        echo -e "\n$pub_ip	$name\n" | sudo tee -ai $f_hosts >> $f_debug;
    fi

    sudo hostname "$name" # Just ensuring that the hostname is correctly set as per the cli prior to install

	# Checking if the hostname of the Security Monkey Instance is in Hostname file
    if grep -Fqi $name $f_hostname;
    then
        echo -e "\nHostname for $pub_ip is $name and is in $f_hostname.\n" >> $f_debug;
    else
        sudo sed -i.bak -e's/ip.*/\$name/i' $f_hostname;
    fi
}

### Install pre-reqs
install_pre ()
{
   sudo apt-get update
   sudo apt-get install -y python-pip python-dev python-psycopg2 libpq-dev nginx supervisor git
   if [[ $db =~ 127.0.0.1 || $db -eq localhost ]];
   then
       echo -e "\nInstalling Postgres on the localhost so must NOT be using a RDS, let's hope so.....\n";
       sudo apt-get install -y postgresql postgresql-contrib 
   else
       echo -e "\nNot installing Postgres on the localhost so must be using a RDS, let's hope so.....\n";
   fi
}

# Create secmonkey db
create_db ()
{
    echo -e "\nWe will now create a Postgres DB user as per your CLI options and you will be prompted for the password....\n"
    sleep 3
    echo "$db_user $db $password"
    psql -U $db_user -h $db -c "alter user $db_user with password '$password';"
    echo -e "\nWe will now create the _secmonkey_ DB user as per your CLI options and you will be re-prompted for the password....\n"
    psql -U $db_user -h $db -c 'CREATE DATABASE secmonkey'
}

###
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

directory="$dir_sm"
environment=PYTHONPATH='\$dir_sm',SECURITY_MONKEY_SETTINGS="$file_deploy"
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

DEFAULT_MAIL_SENDER = '\$sender'
SECURITY_REGISTERABLE = True
SECURITY_CONFIRMABLE = False
SECURITY_RECOVERABLE = False
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = 'gnoSLMMnUIlk2iLhDkW7OgFZ'
SECURITY_POST_LOGIN_VIEW = 'https://$name'

# This address gets all change notifications
SECURITY_TEAM_EMAIL = '\$recipient'
EOF

}

### Cloning the SecurityMonkey repo from Github & Installs SecurityMonkey

clone_install ()
{
    sudo git clone https://github.com/Netflix/security_monkey.git $dir_sm

    cd $dir_sm && sudo python setup.py install

    create_config_file
    
    sudo -E python $dir_sm/manage.py db upgrade 			# Need to keep local environment variables when sudo to python because we need to know where SECURITY_HOME_SETTINGS is. Hence, "-E".
    clear_hist
}

### Automating the creation of the self-signed certificate
# I ripped this off "https://gist.github.com/bradland/1690807", thx :)
# Script accepts a single argument, the fqdn for the cert

fail_if_error()
{
    [ $1 != 0 ] && {
  	unset PASSPHRASE
  	exit 15
  	}
}

create_ss_cert ()
{
    if [ -z "$site" ];
    then
  	    echo -e "Usage: $(basename $0) -s <site>\n";
  	    exit 16
  	fi

# Generate a passphrase
export PASSPHRASE=$(head -c 500 /dev/urandom | tr -dc a-z0-9A-Z | head -c 128; echo)

# Certificate details; replace items in angle brackets with your own info
subj="
C=US
ST=OR
O=Riot Games
localityName=PO
commonName=$site
organizationalUnitName=InfoSec
emailAddress=$email
"

# Generate the server private key
openssl genrsa -des3 -out $site.key -passout env:PASSPHRASE 2048
fail_if_error $?

# Generate the CSR
openssl req \
    -new \
    -batch \
    -subj "$(echo -n "$subj" | tr "\n" "/")" \
    -key $site.key \
    -out $site.csr \
    -passin env:PASSPHRASE
fail_if_error $?
cp $site.key $site.key.org
fail_if_error $?

# Strip the password so we don't have to type it every time we restart nginx
openssl rsa -in $site.key.org -out $site.key -passin env:PASSPHRASE
fail_if_error $?

# Generate the cert (good for 3 years)
openssl x509 -req -days 1095 -in $site.csr -signkey $site.key -out $site.crt
fail_if_error $?
}

### this function configures .ini file & starts the supervisor process

cs_supervisor ()
{
	create_ini_file

    sudo -E supervisord -c $file_ini
    sudo -E supervisorctl -c $file_ini
}

### This function configures nginx
config_nginx ()
{
    sudo mkdir -p $dir_nginx_log
    sudo touch $dir_nginx_log/securitymonkey.access.log
    sudo touch $dir_nginx_log/securitymonkey.error.log
    sudo cp $dir_net/securitymonkey.conf /etc/nginx/sites-available/securitymonkey.conf

    sudo ln -s /etc/nginx/sites-available/securitymonkey.conf /etc/nginx/sites-enabled/securitymonkey.conf # Symlink the available site to the enabled site
    sudo rm /etc/nginx/sites-enabled/default # removing the default site
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

