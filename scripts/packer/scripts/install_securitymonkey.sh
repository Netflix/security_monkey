#/bin/bash

validate_environment() {
    echo "Validating the environment"

    # Basic application settings
    if [ -z "${APP_INSTALL_BASE_DIR}" ]; then echo "Missing APP_INSTALL_BASE_DIR environment variable" && exit -1; fi
    if [ -z "${APP_TMP_BASE_DIR}" ]; then echo "Missing APP_TMP_BASE_DIR environment variable" && exit -1; fi
    if [ -z "${APP_API_PORT}" ]; then echo "Missing APP_API_PORT environment variable" && exit -1; fi
    if [ -z "${APP_BASE_URL_FORMAT}" ]; then echo "Missing APP_BASE_URL_FORMAT environment variable" && exit -1; fi
    if [ -z "${APP_ENVIRONMENT}" ]; then echo "Missing APP_ENVIRONMENT environment variable" && exit -1; fi
    if [ -z "${APP_FQDN}" ]; then echo "Missing APP_FQDN environment variable" && exit -1; fi
    if [ -z "${APP_USE_ROUTE53}" ]; then echo "Missing APP_USE_ROUTE53 environment variable" && exit -1; fi
    if [ -z "${APP_INSTANCE_DETAIL}" ]; then echo "Missing APP_INSTANCE_DETAIL environment variable" && exit -1; fi

    # Log configuration
    if [ -z "${APP_LOG_DIR}" ]; then echo "Missing APP_LOG_DIR environment variable" && exit -1; fi
    if [ -z "${APP_LOG_FILE}" ]; then echo "Missing APP_LOG_FILE environment variable" && exit -1; fi
    if [ -z "${APP_LOG_LEVEL}" ]; then echo "Missing APP_LOG_LEVEL environment variable" && exit -1; fi

    # API, web and nginx configuration
    if [ -z "${APP_USE_NGINX}" ]; then echo "Missing APP_USE_NGINX environment variable" && exit -1; fi
    if [ -z "${APP_NGINX_PORT}" ]; then echo "Missing APP_NGINX_PORT environment variable" && exit -1; fi
    if [ -z "${APP_NGINX_SSL_ENABLED}" ]; then echo "Missing APP_NGINX_SSL_ENABLED environment variable" && exit -1; fi
    if [ -z "${APP_NGINX_SSL_SELF_SIGNED}" ]; then echo "Missing APP_NGINX_SSL_SELF_SIGNED environment variable" && exit -1; fi
    if [ -z "${APP_WEB_PATH}" ]; then echo "Missing APP_WEB_PATH environment variable" && exit -1; fi
    if [ -z "${APP_WEB_PORT}" ]; then echo "Missing APP_WEB_PORT environment variable" && exit -1; fi

    # Only require variables if we are self-signing or not
    if [ "${APP_NGINX_SSL_SELF_SIGNED}" = "True" ]; then
        if [ -z "${APP_NGINX_SSL_SELF_SIGNED_SUBJ}" ]; then echo "Missing APP_NGINX_SSL_SELF_SIGNED_SUBJ environment variable" && exit -1; fi
    else
        if [ -z "${APP_NGINX_SSL_CERT_DATA}" ]; then echo "Missing APP_NGINX_SSL_CERT_DATA environment variable" && exit -1; fi
        if [ -z "${APP_NGINX_SSL_KEY_DATA}" ]; then echo "Missing APP_NGINX_SSL_KEY_DATA environment variable" && exit -1; fi
    fi

    # Scheduler configuration
    if [ -z "${APP_CORE_THREADS}" ]; then echo "Missing APP_CORE_THREADS environment variable" && exit -1; fi
    if [ -z "${APP_MAX_THREADS}" ]; then echo "Missing APP_MAX_THREADS environment variable" && exit -1; fi

    # Database configuration
    if [ -z "${APP_DB_ENDPOINT}" ]; then echo "Missing APP_DB_ENDPOINT environment variable" && exit -1; fi
    if [ -z "${APP_DB_SCHEMA}" ]; then echo "Missing APP_DB_SCHEMA environment variable" && exit -1; fi
    if [ -z "${APP_DB_USERNAME}" ]; then echo "Missing APP_DB_USERNAME environment variable" && exit -1; fi
    if [ -z "${APP_DB_PASSWORD}" ]; then echo "Missing APP_DB_PASSWORD environment variable" && exit -1; fi
    if [ -z "${APP_DB_MAX_OVERFLOW}" ]; then echo "Missing APP_DB_MAX_OVERFLOW environment variable" && exit -1; fi
    if [ -z "${APP_DB_POOL_SIZE}" ]; then echo "Missing APP_DB_POOL_SIZE environment variable" && exit -1; fi

    # Email configuration
    if [ -z "${APP_MAIL_DEFAULT_SENDER}" ]; then echo "Missing APP_MAIL_DEFAULT_SENDER environment variable" && exit -1; fi
    if [ -z "${APP_MAIL_SES_REGION}" ]; then echo "Missing APP_MAIL_SES_REGION environment variable" && exit -1; fi
    if [ -z "${APP_MAIL_USE_SMTP}" ]; then echo "Missing APP_MAIL_USE_SMTP environment variable" && exit -1; fi
    if [ -z "${APP_MAIL_USE_SSL}" ]; then echo "Missing APP_MAIL_USE_SSL environment variable" && exit -1; fi
    if [ -z "${APP_MAIL_PORT}" ]; then echo "Missing APP_MAIL_PORT environment variable" && exit -1; fi
    if [ "${APP_MAIL_USE_SMTP}" = "True" ]; then
        if [ -z "${APP_MAIL_SERVER}" ]; then echo "Missing APP_MAIL_SERVER environment variable" && exit -1; fi
    fi

    # Security configuration
    if [ -z "${APP_SECRET_KEY}" ]; then echo "Missing APP_SECRET_KEY environment variable" && exit -1; fi
    if [ -z "${APP_SEC_PW_HASH}" ]; then echo "Missing APP_SEC_PW_HASH environment variable" && exit -1; fi
    if [ -z "${APP_SEC_PW_SALT}" ]; then echo "Missing APP_SEC_PW_SALT environment variable" && exit -1; fi
    if [ -z "${APP_SEC_CONFIRM}" ]; then echo "Missing APP_SEC_CONFIRM environment variable" && exit -1; fi
    if [ -z "${APP_SEC_RECOVER}" ]; then echo "Missing APP_SEC_RECOVER environment variable" && exit -1; fi
    if [ -z "${APP_SEC_REGISTER}" ]; then echo "Missing APP_SEC_REGISTER environment variable" && exit -1; fi
    if [ -z "${APP_SEC_TEAM_EMAILS}" ]; then echo "Missing APP_SEC_TEAM_EMAILS environment variable" && exit -1; fi

    # WTF CSRF protection settings
    if [ -z "${APP_WTF_CSRF_ENABLED}" ]; then echo "Missing APP_WTF_CSRF_ENABLED environment variable" && exit -1; fi
    if [ -z "${APP_WTF_CSRF_METHODS}" ]; then echo "Missing APP_WTF_CSRF_METHODS environment variable" && exit -1; fi
    if [ -z "${APP_WTF_CSRF_STRICT}" ]; then echo "Missing APP_WTF_CSRF_STRICT environment variable" && exit -1; fi
}

create_dirs() {
    echo "Setting up required folders and files"
    # We need to create /var/www for python-eggs cache
    mkdir -p $APP_LOG_DIR $APP_INSTALL_BASE_DIR /var/www

    touch $APP_LOG_DIR/security_monkey.error.log
    touch $APP_LOG_DIR/security_monkey.access.log
    touch $APP_LOG_DIR/$APP_LOG_FILE

    chown -R www-data $APP_LOG_DIR $APP_LOG_DIR /var/www
}

install_prereqs() {
    echo "Installing dart debian mirrors"
    if [ ! -f /etc/apt/sources.list.d/dart_stable.list ]; then
        curl --silent https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add - 1>&1 2>&2
        curl --silent https://storage.googleapis.com/download.dartlang.org/linux/debian/dart_stable.list > /etc/apt/sources.list.d/dart_stable.list 1>&1 2>&2
    fi

    # Install packages required
    echo "Updating apt and installing required packages"
    apt-get update
    apt-get install -y python-pip python-dev python-psycopg2 libpq-dev supervisor git python-m2crypto dart nginx libffi-dev
}

install_secmonkey() {
    echo "Fetching security monkey code and installing it"
    cd $APP_INSTALL_BASE_DIR
    if [ ! -d security_monkey ]; then
        git clone --depth 1 --branch master https://github.com/Netflix/security_monkey.git 1>&1 2>&2
        cd security_monkey
        python setup.py install 1>&1 2>&2
    else
        echo "Skipping git clone, already cloned"
    fi
}

build_webapp() {
    echo "Building dart web-app"
    mkdir -p $APP_INSTALL_BASE_DIR/security_monkey/security_monkey/static
    cd $APP_INSTALL_BASE_DIR/security_monkey/dart
    /usr/lib/dart/bin/pub get
    /usr/lib/dart/bin/pub build
    cp -a $APP_INSTALL_BASE_DIR/security_monkey/dart/build/web/* $APP_INSTALL_BASE_DIR/security_monkey/security_monkey/static
}

update_configs() {
    echo "Updating security monkey config-deploy.py and supervisor configs"
    CFG_DEPLOY="$APP_INSTALL_BASE_DIR/security_monkey/env-config/config-deploy.py"
    
    # Escape a few of the variables to prevent bad sed replacements
    SAFE_DB_PW=$(sed -e 's/[\/&^]/\\&/g' <<< ${APP_DB_PASSWORD})
    SAFE_MAIL_PW=$(sed -e 's/[\/&^]/\\&/g' <<< ${APP_MAIL_PASSWORD})
    SAFE_SECRET=$(sed -e 's/[\/&^]/\\&/g' <<< ${APP_SECRET_KEY})
    SAFE_SALT=$(sed -e 's/[\/&^]/\\&/g' <<< ${APP_SEC_PW_SALT})

    sed -e "s^APP_API_PORT^${APP_API_PORT}^g" \
        -e "s^APP_BASE_URL_FORMAT^${APP_BASE_URL_FORMAT}^g" \
        -e "s^APP_ENVIRONMENT^${APP_ENVIRONMENT}^g" \
        -e "s^APP_FQDN^${APP_FQDN}^g" \
        -e "s^APP_USE_ROUTE53^${APP_USE_ROUTE53}^g" \
        -e "s^APP_INSTANCE_DETAIL^${APP_INSTANCE_DETAIL}^g" \
        -e "s^APP_LOG_DIR^${APP_LOG_DIR}^g" \
        -e "s^APP_LOG_FILE^${APP_LOG_FILE}^g" \
        -e "s^APP_LOG_LEVEL^${APP_LOG_LEVEL}^g" \
        -e "s^APP_USE_NGINX^${APP_USE_NGINX}^g" \
        -e "s^APP_NGINX_PORT^${APP_NGINX_PORT}^g" \
        -e "s^APP_NGINX_SSL_ENABLED^${APP_NGINX_SSL_ENABLED}^g" \
        -e "s^APP_WEB_PATH^${APP_WEB_PATH}^g" \
        -e "s^APP_WEB_PORT^${APP_WEB_PORT}^g" \
        -e "s^APP_CORE_THREADS^${APP_CORE_THREADS}^g" \
        -e "s^APP_MAX_THREADS^${APP_MAX_THREADS}^g" \
        -e "s^APP_DB_ENDPOINT^${APP_DB_ENDPOINT}^g" \
        -e "s^APP_DB_SCHEMA^${APP_DB_SCHEMA}^g" \
        -e "s^APP_DB_USERNAME^${APP_DB_USERNAME}^g" \
        -e "s^APP_DB_PASSWORD^${SAFE_DB_PW}^g" \
        -e "s^APP_DB_MAX_OVERFLOW^${APP_DB_MAX_OVERFLOW}^g" \
        -e "s^APP_DB_POOL_SIZE^${APP_DB_POOL_SIZE}^g" \
        -e "s^APP_MAIL_DEFAULT_SENDER^${APP_MAIL_DEFAULT_SENDER}^g" \
        -e "s^APP_MAIL_SES_REGION^${APP_MAIL_SES_REGION}^g" \
        -e "s^APP_MAIL_USE_SMTP^${APP_MAIL_USE_SMTP}^g" \
        -e "s^APP_MAIL_USE_SSL^${APP_MAIL_USE_SSL}^g" \
        -e "s^APP_MAIL_SERVER^${APP_MAIL_SERVER}^g" \
        -e "s^APP_MAIL_PORT^${APP_MAIL_PORT}^g" \
        -e "s^APP_MAIL_USERNAME^${APP_MAIL_USERNAME}^g" \
        -e "s^APP_MAIL_PASSWORD^${SAFE_DB_PW}^g" \
        -e "s^APP_SECRET_KEY^${SAFE_SECRET}^g" \
        -e "s^APP_SEC_PW_HASH^${APP_SEC_PW_HASH}^g" \
        -e "s^APP_SEC_PW_SALT^${SAFE_SALT}^g" \
        -e "s^APP_SEC_CONFIRM^${APP_SEC_CONFIRM}^g" \
        -e "s^APP_SEC_RECOVER^${APP_SEC_RECOVER}^g" \
        -e "s^APP_SEC_REGISTER^${APP_SEC_REGISTER}^g" \
        -e "s^APP_SEC_TEAM_EMAILS^${APP_SEC_TEAM_EMAILS}^g" \
        -e "s^APP_WTF_CSRF_ENABLED^${APP_WTF_CSRF_ENABLED}^g" \
        -e "s^APP_WTF_CSRF_METHODS^${APP_WTF_CSRF_METHODS}^g" \
        -e "s^APP_WTF_CSRF_STRICT^${APP_WTF_CSRF_STRICT}^g" \
        $APP_TMP_BASE_DIR/files/config.py > $CFG_DEPLOY

    # Setup Supervisor
    sed -e "s^APP_INSTALL_BASE_DIR^${APP_INSTALL_BASE_DIR}^g" \
        $APP_TMP_BASE_DIR/files/supervisor.conf > /etc/supervisor/conf.d/security_monkey.conf
}

install_certs() {
    if [ "${APP_NGINX_SSL_ENABLED}" = "True" ]; then
        if [ "${APP_NGINX_SSL_SELF_SIGNED}" = "True" ]; then
            echo "Generating and installing self-signed certificates"

            export PASSPHRASE=$(head -c 500 /dev/urandom | LC_CTYPE=C tr -dc a-z0-9A-Z | head -c 128; echo)
            openssl genrsa -des3 -out server_p.key -passout env:PASSPHRASE 2048
            openssl req -new -batch -subj "$APP_NGINX_SSL_SELF_SIGNED_SUBJ" -key server_p.key -out server.csr -passin env:PASSPHRASE
            openssl rsa -in server_p.key -out server.key -passin env:PASSPHRASE
            openssl x509 -req -days 3650 -in server.csr -signkey server.key -out server.crt

            mv server.crt /etc/ssl/certs/secmonkey.crt
            mv server.key /etc/ssl/private/secmonkey.key
        else
            echo "Installing provided SSL certifictes"
            CERTDATA=$(echo "${APP_NGINX_SSL_CERT_DATA}" | base64 -d)
            KEYDATA=$(echo "${APP_NGINX_SSL_KEY_DATA}" | base64 -d)

            echo "$CERTDATA" > /etc/ssl/certs/secmonkey.crt
            echo "$KEYDATA" > /etc/ssl/certs/secmonkey.key
        fi
    else
        echo "SSL disabled, not generating or installing certificates"
    fi
}

configure_nginx() {
    echo "Configuring nginx"

    if [ "${APP_NGINX_SSL_ENABLED}" = "True" ]; then
        sed -e "s^APP_INSTALL_BASE_DIR^${APP_INSTALL_BASE_DIR}^g" \
            -e "s^APP_NGINX_PORT^${APP_NGINX_PORT}^g" \
            -e "s^APP_API_PORT^${APP_API_PORT}^g" \
            -e "s^APP_LOG_DIR^${APP_LOG_DIR}^g" \
            $APP_TMP_BASE_DIR/files/nginx-ssl.conf > /etc/nginx/sites-available/securitymonkey.conf
    else
        sed -e "s^APP_INSTALL_BASE_DIR^${APP_INSTALL_BASE_DIR}^g" \
            -e "s^APP_NGINX_PORT^${APP_NGINX_PORT}^g" \
            -e "s^APP_API_PORT^${APP_API_PORT}^g" \
            -e "s^APP_LOG_DIR^${APP_LOG_DIR}^g" \
            $APP_TMP_BASE_DIR/files/nginx-nossl.conf > /etc/nginx/sites-available/securitymonkey.conf
    fi

    if [ -h /etc/nginx/sites-enabled/default ]; then
        rm -f /etc/nginx/sites-enabled/default;
    fi

    if [ ! -h /etc/nginx/sites-enabled/securitymonkey.conf ]; then
        ln -s /etc/nginx/sites-available/securitymonkey.conf /etc/nginx/sites-enabled/securitymonkey.conf
    fi
    service nginx restart 1>&1 2>&2
}

validate_environment
create_dirs
install_prereqs
install_secmonkey
build_webapp
update_configs
install_certs
configure_nginx

echo "Finished installing Security Monkey"
