#!/bin/bash

# Wait the database
sleep 10

sudo -u ${SECURITY_MONKEY_POSTGRES_USER:-postgres} psql\
    -h ${SECURITY_MONKEY_POSTGRES_HOST:-postgres} -p ${SECURITY_MONKEY_POSTGRES_PORT:-5432}\
    --command "ALTER USER ${SECURITY_MONKEY_POSTGRES_USER:-postgres} with PASSWORD '${SECURITY_MONKEY_POSTGRES_PASSWORD:-securitymonkeypassword}';"

sudo -u ${SECURITY_MONKEY_POSTGRES_USER:-postgres} createdb\
    -h ${SECURITY_MONKEY_POSTGRES_HOST:-postgres} -p ${SECURITY_MONKEY_POSTGRES_PORT:-5432}\
    -O ${SECURITY_MONKEY_POSTGRES_USER:-postgres} ${SECURITY_MONKEY_POSTGRES_DATABASE:-secmonkey}

mkdir -p /var/log/security_monkey/
touch "/var/log/security_monkey/security_monkey-deploy.log"

cd /usr/local/src/security_monkey
python manage.py db upgrade

cat <<EOF | python manage.py create_user "admin@example.org" "Admin"
${SECURITY_MONKEY_PASSWORD:-admin}
${SECURITY_MONKEY_PASSWORD:-admin}
EOF
