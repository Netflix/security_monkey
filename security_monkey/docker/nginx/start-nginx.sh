#!/usr/bin/env bash

SECURITY_MONKEY_SSL_CERT=${SECURITY_MONKEY_SSL_CERT:-/etc/nginx/ssl/server.crt}
SECURITY_MONKEY_SSL_KEY=${SECURITY_MONKEY_SSL_KEY:-/etc/nginx/ssl/server.key}

# if no SSL, disable HTTPS (if not already disabled)
if ([ ! -f "$SECURITY_MONKEY_SSL_CERT" ] || [ ! -f "$SECURITY_MONKEY_SSL_KEY" ]) && grep -E '^[^#]+ssl' /etc/nginx/conf.d/securitymonkey.conf; then
    echo "$(date) Error: Missing files required for SSL"
    sed -i.bak '/^#/! s/.*ssl/# &/' /etc/nginx/conf.d/securitymonkey.conf &&\
    echo "$(date) Warn: Disabled ssl in securitymonkey.conf"
fi

exec nginx
