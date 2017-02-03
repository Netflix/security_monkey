Docker Instructions
===================

The docker-compose.yml file describes the SecurityMonkey environment. This is intended for local development with the intention of deploying SecurityMonkey containers with a Docker Orchestration tool like Kubernetes.

The Dockerfile builds SecurityMonkey into a container with several different entrypoints. These are for the different responsibilities SecurityMonkey has.
Also, the docker/nginx/Dockerfile file is used to build an NGINX container that will front the API, serve the static assets, and provide TLS.

Quick Start:
------------
Define your specific settings in **secmonkey.env** file. For example, this file will look like::

  AWS_ACCESS_KEY_ID=
  AWS_SECRET_ACCESS_KEY=
  SECURITY_MONKEY_POSTGRES_HOST=postgres
  SECURITY_MONKEY_FQDN=192.168.99.100

Next, you can build all the containers by running::

  $ docker-compose build

The database is then started via::

  $ docker-compose up -d postgres

On a fresh database instance, various initial configuration must be run such as database setup, initial user creation, etc. You can run the ``init`` container via::

  $ docker-compose up -d init

See the section below for more details.

Now that the database is setup, you can start up the remaining containers (Security Monkey, nginx, and the scheduler) via::

  $ docker-compose up

Commands:
---------
::

  $ docker-compose build [api | scheduler | nginx | init]

  $ docker-compose up -d [postgres | api | scheduler | nginx | init]

More Info:
----------
::

  $ docker-compose up -d init

The init container is where the SecurityMonkey code is available for you to run manual configurations such as::

  $ python manage.py create_user admin@example.com Admin

and/or::

  $ python manage.py add_account --number $account --name $name -r SecurityMonkey

The init container provides a sandbox and is useful for local development. It is not required otherwise.
