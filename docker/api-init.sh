#!/bin/bash -e

# Wait the database
sleep 10

echo "Starting API init on $( date )"

echo "Creating the user: ${SECURITY_MONKEY_POSTGRES_USER:-postgres} on ${SECURITY_MONKEY_POSTGRES_HOST:-postgres}:${SECURITY_MONKEY_POSTGRES_PORT:-5432}:"
psql -h ${SECURITY_MONKEY_POSTGRES_HOST:-postgres} -p ${SECURITY_MONKEY_POSTGRES_PORT:-5432} \
    -U ${SECURITY_MONKEY_POSTGRES_USER:-postgres} \
    --command "ALTER USER ${SECURITY_MONKEY_POSTGRES_USER:-postgres} with PASSWORD '${SECURITY_MONKEY_POSTGRES_PASSWORD:-securitymonkeypassword}';"

echo "Creating the ${SECURITY_MONKEY_POSTGRES_DATABASE:-secmonkey} on ${SECURITY_MONKEY_POSTGRES_HOST:-postgres}:${SECURITY_MONKEY_POSTGRES_PORT:-5432} with the ${SECURITY_MONKEY_POSTGRES_USER:-postgres}:"
createdb -h ${SECURITY_MONKEY_POSTGRES_HOST:-postgres} -p ${SECURITY_MONKEY_POSTGRES_PORT:-5432} \
    -U ${SECURITY_MONKEY_POSTGRES_USER:-postgres} \
    -O ${SECURITY_MONKEY_POSTGRES_USER:-postgres} ${SECURITY_MONKEY_POSTGRES_DATABASE:-secmonkey}

mkdir -p /var/log/security_monkey/
touch "/var/log/security_monkey/security_monkey-deploy.log"

cd /usr/local/src/security_monkey
monkey db upgrade

# -------------ADD ADDITIONAL MONKEY COMMANDS TO EXECUTE HERE-------------

cat <<EOF | monkey create_user "admin@example.org" "Admin"
${SECURITY_MONKEY_PASSWORD:-admin}
${SECURITY_MONKEY_PASSWORD:-admin}
EOF

# -------------ADD MONKEY COMMANDS ABOVE TO ADD ACCOUNTS AND DO OTHER THINGS-------------

echo "Completed API init on $( date )"
