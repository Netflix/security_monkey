Docker Instructions
===================

The docker-compose.yml file describes the SecurityMonkey environment. This is intended for local development with the intention of deploying SecurityMonkey containers with a Docker Orchestration tool like Kubernetes.

The Dockerfile builds SecurityMonkey into a container with several different entrypoints. These are for the different responsibilities SecurityMonkey has. Also, the docker/nginx/Dockerfile file is used to build an NGINX container that will front the API, serve the static assets, and provide TLS.

Quick Start:
------------

Define your specific settings in **secmonkey.env** file. For example, this file will look like:

    AWS_ACCESS_KEY_ID=
    AWS_SECRET_ACCESS_KEY=
    SECURITY_MONKEY_POSTGRES_HOST=postgres
    SECURITY_MONKEY_FQDN=127.0.0.1
    # Must be false if HTTP
    SESSION_COOKIE_SECURE=False


**Please note** to be able to run the scheduler inheriting the SecurityMonkeyInstanceProfile IAM Role, the AWS credentials have to be removed from config file above (secmonkey.env) otherwise boto3 inside the scheduler container won't escalate to SecurityMonkeyInstanceProfile because will try to use empty AWS credentials instead.


Next, you can build all the containers by running:

    $ docker-compose build

On a fresh database instance, various initial configuration must be run such as database setup, initial user creation (<admin@example.org> / admin), etc. You can run the `init` container via:

    $ docker-compose -f docker-compose.init.yml up -d

Before you bring the containers up, you need to add an AWS account for the scheduler to monitor:

    $ monkey add_account_aws --id $account --name $name -r SecurityMonkey

Now that the database is setup, you can start up the remaining containers (Security Monkey, nginx, and the scheduler) via:

    $ docker-compose up -d

You can stop the containers with:

    $ docker-compose stop

Otherwise you can shutdown and clean the images and volumes with:

    $ docker-compose down

Commands:
---------

    $ docker-compose build [api | scheduler | nginx | data]

    $ docker-compose up -d [postgres | api | scheduler | nginx | data]

    $ docker-compose restart [postgres | api | scheduler | nginx | data]

    $ docker-compose stop

    $ docker-compose down

More Info:
----------

You can get a shell thanks to the docker-compose.shell.yml override:

    $ docker-compose -f docker-compose.yml -f docker-compose.shell.yml up -d data
    $ docker attach $(docker ps -aqf "name=secmonkey-data")

This allows you to access SecurityMonkey code, and run manual configurations such as:

    $ monkey create_user admin@example.com Admin

and/or:

    $ monkey add_account_aws --id $account --name $name -r SecurityMonkey

This container is useful for local development. It is not required otherwise.

Tips and tricks:
----------------

If you have to restart the scheduler, you don't have to restart all the stack. Just run:

    $ docker-compose restart scheduler

If you want to persist the DB data, create a postgres-data directory in the repository root:

    $ mkdir postgres-data

and uncomment these two lines in docker-compose.yml (in the postgres section):

    #volumes:
    #    - ./postgres-data/:/var/lib/postgresql/data
