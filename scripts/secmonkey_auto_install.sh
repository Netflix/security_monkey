#!/bin/bash
########################################################################################################
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
########################################################################################################
#
# Bash script to automate installation of Security Monkey.
#
# This script assumes that you're going to run Security Monkey on an Ubuntu EC2 Instance in AWS.
#
# This script will work for a Postgres DB installation on both RDS and localhost.
#
# Written by :: markofu <marko@hillick.net>
# Date :: September 2014
#
# Improved and Tidied by :: cbarrac
# Date :: August 2015
#
# Version History :: 
#
#
#       0.1 :: 2014/09/16        :: First version submitted to Netflix Develop Branch. Few issues.
#       0.2 :: 2014/10/02        :: Fixed a few aesthetics.
#       0.3 :: 2014/10/16        :: Config-deploy file now takes in any user & usage recommendations.
#                                   Removing the Postgres password prompt.
#       0.4 :: 2014/10/30        :: Removing the supervisorctl commands as not required.
#       0.5 :: 2015/08/11-12     :: Modified supervisor file name & updated package contents to reflect
#                                   changes since Dart & Angular JS.
#       0.5.1 :: 2015/08/24-25   :: Typos, ownership & SECURITY_TEAM_EMAIL should be an array.
#       0.5.2 :: 2015/09/01      :: Update for v0.3.8. Add dart support. Some cleanup.
#       0.5.3 :: 2015/10/13      :: Created error and echo_usage functions for simplification.
#       0.5.4 :: 2015/11/20      :: Pinned dart to dart=1.12.2-1
#       0.5.5 :: 2016/06/09      :: Removed dart pinning. Modified logging configuration. 
#
# To Do :: 
#         Fix bug with password containing !
#
########################################################################################################
 
set -e 

### Declaring some variables

USAGE="Usage: ./$(basename $0) [-hv] [-d arg] [-e arg] [-i arg] [-n arg] [-p arg] [-r arg] [-s arg] [-u arg] [-w arg].

Ensure that the script is executable, for example, with permissions of 755 (rwxr_xr_x) using 'chmod 755 $(basename $0)'

For example - 

              ./$(basename $0) -d 10.11.1.11 -e cert_email@secmonkey.com -i 10.10.10.10 -n ec2-10-10-10-10.us-west-1.compute.amazonaws.com -p SuperSecretPasswordYo -r recipient@secmonkey.com -s sender@secmonkey.com -u postgres -w secmonkey.com
    
              ./$(basename $0) -h 

              ./$(basename $0) -v
    

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
              -v  >> Version of the $(basename $0) script
              -w  >> Site (Domain) be used for the self-signed certificate
    "

VERSION="0.5.4"
ARGS=$#

err_code=10
f_hosts="/etc/hosts"
f_hostname="/etc/hostname"
f_lsb="/etc/lsb-release"
f_debug="/var/tmp/sec_monkey_install_debug.log"
f_nginx_site_a="/etc/nginx/sites-available/securitymonkey.conf"
f_nginx_site_e="/etc/nginx/sites-enabled/securitymonkey.conf"
f_nginx_default="/etc/nginx/sites-enabled/default"
f_pgpass="$HOME/.pgpass"

### Function to check that the script is being run with options.

check_opt ()
{
    if [ $ARGS -eq 0 ]
    then
        error "Please run with valid options! Help is printed with '-h'."
        echo_usage
    elif [ $ARGS -gt 20 ]
    then
        error "Please examine the usage options for this script - you can only have a maximum of 7 command line switches!" && echo_usage
    fi
}

### Function to check that the script only runs with appropriate options when looking for help or version

check_opt_one ()
{
    if [ $ARGS -gt 2 ]
    then 
        error "Please run with only one option! Help is printed with '-h'."
        echo_usage
    fi
}

### Function to parse cli options

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
                 echo_usage
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
             -o|--organization) # Organization to be used for the self-signed certificate
                 organization=$2
                 shift 2
                 ;;
        esac
    done
}

### Function to set locales as it's typically screwed up in Ubuntu on AWS after inital install

fix_locales ()
{
	export LANGUAGE=en_US.UTF-8
	export LANG=en_US.UTF-8
	export LC_ALL=en_US.UTF-8
	/usr/sbin/locale-gen en_US.UTF-8
	sudo dpkg-reconfigure locales
}

### Function to set locales as it's typically screwed up in Ubuntu on AWS after inital install
error ()
{
    >&2 echo -e "\nError": $1
    ($err_code++) && exit $(expr $err_code - 1) 
}

### Function to echo Usage Example
echo_usage ()
{
    echo -e "\n$USAGE\n"
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
    file_deploy="$dir_config/config.py"
    file_ini="$dir_super/security_monkey.conf"
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
        error "You don't seem to be running a Ubuntu distro, sorry :( Please only run this on Ubuntu! Now exiting....."
    fi
}

### Function to set hostnname etc
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
        sudo sed -i.bak -e"s/ip.*/\${name}/i" $f_hostname
    fi
}

### Function to install pre-reqs

install_post ()
{
    echo -e "\nInstalling Postgres on the localhost so must NOT be using a RDS, let's hope so.....\n"
    sudo apt-get install -y postgresql postgresql-contrib 
}

install_pre ()
{
    sudo apt-get update && sudo apt-get install -y python-pip python-dev python-psycopg2 libpq-dev nginx supervisor git postgresql-client libyaml-dev libffi-dev libxml2-dev libxmlsec1-dev
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

# Function to connect to the 'postgres' db (assumed to be your default db)
# Modify user password and create secmonkey db
create_db ()
{
    echo -e "Creating a .pgpass file in the home directory to remove the password prompt for the psql commands....\n"
	
    echo "$db:5432:postgres:$user:$password" > $f_pgpass && chmod 0600 $f_pgpass # Postgres DB on RDS always listens on tcp 5432, I currently don't believe it's necessary to change the listening port to a variable from the cli & connecting to the 'postgres' db

    echo -e "We will now create a Postgres DB user as per your CLI options....\n"

    psql -U $user -d postgres -h $db -c "alter user $user with password '$password';" -w
    sleep 3

    existing_db="$(psql -U $user -h $db -d postgres -t -c "SELECT datname FROM pg_database WHERE datname = 'secmonkey'")"
    if [[ "$existing_db" != " secmonkey" ]]; then
      echo -e "\nWe will now create the _secmonkey_ DB user as per your CLI options....\n"
      psql -U $user -h $db -d postgres -c 'CREATE DATABASE secmonkey' -w
    else
      echo "Existing database detected, so using it"
    fi
    rm $f_pgpass # Clearing up after and removing the Postgres password file
}

# The following functions are used to create the security_monkey.ini and config_deploy.py files respectively.
# They are called subsequently by various db scripts

create_ini_file ()
{
    sudo rm $file_ini

cat << EOF | sudo tee -ai $file_ini
[unix_http_server]
file=/tmp/supervisor.sock

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface

[supervisord]
logfile=/tmp/securitymonkey.log
logfile_maxbytes=50MB
logfile_backups=2
loglevel=trace
pidfile=/tmp/supervisord.pid
nodaemon=false
minfds=64000
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
    SECRET_KEY=$(head -c 200 /dev/urandom | tr -dc a-z0-9A-Z | head -c 32; echo)
    SECURITY_PASSWORD_SALT=$(head -c 200 /dev/urandom | tr -dc a-z0-9A-Z | head -c 32; echo)

cat << EOF | sudo tee -ai $file_deploy
# Insert any config items here.
# This will be fed into Flask/SQLAlchemy inside security_monkey/__init__.py

LOG_CFG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
        }
    },
    'handlers': {
        'file': {
            # 'class': 'logging.handlers.RotatingFileHandler',
            'class': 'logging.handlers.GroupWriteRotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': 'security_monkey-deploy.log',
            'maxBytes': 10485760,
            'backupCount': 100,
            'encoding': 'utf8'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'security_monkey': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG'
        },
        'apscheduler': {
            'handlers': ['file', 'console'],
            'level': 'INFO'
        }
    }
}

SQLALCHEMY_DATABASE_URI = 'postgresql://$user:$password@$db:5432/secmonkey'

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

SECRET_KEY = '${SECRET_KEY}'

MAIL_DEFAULT_SENDER = '$sender'
SECURITY_REGISTERABLE = False
SECURITY_CONFIRMABLE = False
SECURITY_RECOVERABLE = False
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = '${SECURITY_PASSWORD_SALT}'
SECURITY_POST_LOGIN_VIEW = 'https://$name'

# This address gets all change notifications
SECURITY_TEAM_EMAIL = ['$recipient']

WTF_CSRF_ENABLED = True
WTF_CSRF_SSL_STRICT = True # Checks Referer Header. Set to False for API access.
WTF_CSRF_METHODS = ['DELETE', 'POST', 'PUT', 'PATCH']

# "NONE", "SUMMARY", or "FULL"
SECURITYGROUP_INSTANCE_DETAIL = 'FULL'

# Threads used by the scheduler.
# You will likely need at least one core thread for every account being monitored.
CORE_THREADS = 25
MAX_THREADS = 30

# SSO SETTINGS:
ACTIVE_PROVIDERS = []  # "ping", "google" or "onelogin"

PING_NAME = ''  # Use to override the Ping name in the UI.
PING_REDIRECT_URI = "{BASE}api/1/auth/ping".format(BASE=BASE_URL)
PING_CLIENT_ID = ''  # Provided by your administrator
PING_AUTH_ENDPOINT = ''  # Often something ending in authorization.oauth2
PING_ACCESS_TOKEN_URL = ''  # Often something ending in token.oauth2
PING_USER_API_URL = ''  # Often something ending in idp/userinfo.openid
PING_JWKS_URL = ''  # Often something ending in JWKS
PING_SECRET = ''  # Provided by your administrator

GOOGLE_CLIENT_ID = ''
GOOGLE_AUTH_ENDPOINT = ''
GOOGLE_SECRET = ''

ONELOGIN_APP_ID = '<APP_ID>'  # OneLogin App ID provider by your administrator
ONELOGIN_EMAIL_FIELD = 'User.email'  # SAML attribute used to provide email address
ONELOGIN_DEFAULT_ROLE = 'View'  # Default RBAC when user doesn't already exist
ONELOGIN_HTTPS = True  # If using HTTPS strict mode will check the requests are HTTPS
ONELOGIN_SETTINGS = {
    # If strict is True, then the Python Toolkit will reject unsigned
    # or unencrypted messages if it expects them to be signed or encrypted.
    # Also it will reject the messages if the SAML standard is not strictly
    # followed. Destination, NameId, Conditions ... are validated too.
    "strict": True,

    # Enable debug mode (outputs errors).
    "debug": True,

    # Service Provider Data that we are deploying.
    "sp": {
        # Identifier of the SP entity  (must be a URI)
        "entityId": "{BASE}metadata/".format(BASE=BASE_URL),
        # Specifies info about where and how the <AuthnResponse> message MUST be
        # returned to the requester, in this case our SP.
        "assertionConsumerService": {
            # URL Location where the <Response> from the IdP will be returned
            "url": "{BASE}api/1/auth/onelogin?acs".format(BASE=BASE_URL),
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports this endpoint for the
            # HTTP-POST binding only.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        },
        # If you need to specify requested attributes, set a
        # attributeConsumingService. nameFormat, attributeValue and
        # friendlyName can be omitted
        #"attributeConsumingService": {
        #        "ServiceName": "SP test",
        #        "serviceDescription": "Test Service",
        #        "requestedAttributes": [
        #            {
        #                "name": "",
        #                "isRequired": False,
        #                "nameFormat": "",
        #                "friendlyName": "",
        #                "attributeValue": ""
        #            }
        #        ]
        #},
        # Specifies info about where and how the <Logout Response> message MUST be
        # returned to the requester, in this case our SP.
        "singleLogoutService": {
            # URL Location where the <Response> from the IdP will be returned
            "url": "{BASE}api/1/auth/onelogin?sls".format(BASE=BASE_URL),
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports the HTTP-Redirect binding
            # only for this endpoint.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        # Specifies the constraints on the name identifier to be used to
        # represent the requested subject.
        # Take a look on src/onelogin/saml2/constants.py to see the NameIdFormat that are supported.
        "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
        # Usually x509cert and privateKey of the SP are provided by files placed at
        # the certs folder. But we can also provide them with the following parameters
        "x509cert": "",
        "privateKey": ""
    },

    # Identity Provider Data that we want connected with our SP.
    "idp": {
        # Identifier of the IdP entity  (must be a URI)
        "entityId": "https://app.onelogin.com/saml/metadata/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID),
        # SSO endpoint info of the IdP. (Authentication Request protocol)
        "singleSignOnService": {
            # URL Target of the IdP where the Authentication Request Message
            # will be sent.
            "url": "https://app.onelogin.com/trust/saml2/http-post/sso/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID),
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports the HTTP-Redirect binding
            # only for this endpoint.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        # SLO endpoint info of the IdP.
        "singleLogoutService": {
            # URL Location of the IdP where SLO Request will be sent.
            "url": "https://app.onelogin.com/trust/saml2/http-redirect/slo/{APP_ID}".format(APP_ID=ONELOGIN_APP_ID),
            # SAML protocol binding to be used when returning the <Response>
            # message. OneLogin Toolkit supports the HTTP-Redirect binding
            # only for this endpoint.
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        # Public x509 certificate of the IdP
        "x509cert": "<ONELOGIN_APP_CERT>"
    }
}

from datetime import timedelta
PERMANENT_SESSION_LIFETIME=timedelta(minutes=60)   # Will logout users after period of inactivity.
SESSION_REFRESH_EACH_REQUEST=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
PREFERRED_URL_SCHEME='https'

REMEMBER_COOKIE_DURATION=timedelta(minutes=60)  # Can make longer if you want remember_me to be useful
REMEMBER_COOKIE_SECURE=True
REMEMBER_COOKIE_HTTPONLY=True

# Log SSL Cert SubjectAltName errors
LOG_SSL_SUBJ_ALT_NAME_ERRORS = True

EOF

}

### Function to clone the SecurityMonkey repo from Github & install SecurityMonkey

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
        echo_usage
    fi
    
    if [ -z "$organization" ]
    then
        organization = "Security Monkey"
    fi

# Generate a passphrase
PASSPHRASE=$(head -c 500 /dev/urandom | tr -dc a-z0-9A-Z | head -c 128; echo)

# Certificate details
subj="
C=US
ST=OR
O=$organization
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
echo -e "\nStripping the password from the site key.....\n"
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

### Function to install Dart and build static website content 
build_static () 
{
    curl https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    curl https://storage.googleapis.com/download.dartlang.org/linux/debian/dart_stable.list > dart_stable.list
    sudo mv dart_stable.list /etc/apt/sources.list.d/dart_stable.list
    sudo apt-get update
    sudo apt-get install -y dart

    cd /apps/security_monkey/dart
    /usr/lib/dart/bin/pub get
    /usr/lib/dart/bin/pub build
    mkdir -p /apps/security_monkey/security_monkey/static
    cp -R /apps/security_monkey/dart/build/web/* /apps/security_monkey/security_monkey/static/
    sudo chown -R ubuntu:ubuntu $dir_sm
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

build_static

cs_supervisor

create_ss_cert

config_nginx
