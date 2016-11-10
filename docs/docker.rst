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

  $ docker-compose build
  ``this will locally build all the containers necessary``
  
  $ docker-compose up -d postgres
  ``this will start the database container``

  $ docker-compose up -d init
  ``this will start a container in which you canuse to setup the database, create users, and other manual configurations, see the below section for more info``

  $ docker-compose up
  ``this will bring up the remaining containers (scheduler and nginx)``

Commands:
---------
  
  $ docker-compose build ``[api | scheduler | nginx | init]``

  $ docker-compose up -d ``[postgres | api | scheduler | nginx | init]``

More Info:
----------
::

  $ docker-compose up -d init

The init container is where the SecurityMonkey code is available for you to run manual configurations such as::

  $ python manage.py create_user admin@example.com Admin

and/or::

  $ python manage.py add_account --number $account --name $name -r SecurityMonkey

The init container provides a sandbox and is useful for local development. It is not required otherwise.
