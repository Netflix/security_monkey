#!/usr/bin/env bash

SECURITY_MONKEY_SSL_CERT=${SECURITY_MONKEY_SSL_CERT:-/etc/nginx/ssl/server.crt}
SECURITY_MONKEY_SSL_KEY=${SECURITY_MONKEY_SSL_KEY:-/etc/nginx/ssl/server.key}
SECURITY_MONKEY_CONF=${SECURITY_MONKEY_CONF:-/etc/nginx/conf.d/securitymonkey.conf}

if [ ! -f "$SECURITY_MONKEY_SSL_CERT" ] || [ ! -f "$SECURITY_MONKEY_SSL_KEY" ]; then
    # comment out ssl configurations when cert and key are not found
    sed -i.bak 's@^\s*listen.*ssl.*$@#&@' $SECURITY_MONKEY_CONF
    sed -i.bak 's@^\s.*ssl_certificate.*$@#&@' $SECURITY_MONKEY_CONF
fi

exec nginx
