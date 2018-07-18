Docker Instructions
===================

The `docker-compose.yml` file describes the SecurityMonkey environment. This is intended for local development with the intention of deploying Security Monkey containers with a Docker Orchestration tool like Kubernetes.

The `Dockerfile` builds Security Monkey into a container with several different entrypoints. These are for the different responsibilities Security Monkey has. Also, the `docker/nginx/Dockerfile` file is used to build an NGINX container that will front the API, serve the static assets, and provide TLS.

Recommend `docker>=17.12.1` and `docker-compose>=1.18.0` versions.

Quick Start:
------------

1. Define your specific settings in the **`secmonkey.env`** file. For example, this file will look like:

        AWS_ACCESS_KEY_ID=INSERTHERE
        AWS_SECRET_ACCESS_KEY=INSERTHERE
        SECURITY_MONKEY_POSTGRES_HOST=postgres
        SECURITY_MONKEY_FQDN=127.0.0.1
        # Must be false if HTTP
        SESSION_COOKIE_SECURE=False

    **Please note:** The `secmonkey.env` file's values for the `AWS_ACCESS_KEY_ID` and the `AWS_SECRET_ACCESS_KEY` have priority on the credentials utilized in the container.
    Thus, if you are reliant on another mechanism for injecting AWS Credentials into your container, you MUST remove or comment out the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
    from `secmonkey.env`.

1. Build all the containers by running:

        $ docker-compose build

3. On a fresh database instance, various initial configuration must be run such as database setup, initial user creation (<admin@example.org> / admin), etc.
You can make additional Docker configuration changes by modifying `docker-compose.init.yml`. Additionally, before you bring the containers up,
you need to add an account for the scheduler to monitor. This can all be done one of two ways:
    1. By modifying the `docker/api-init.sh` script to include the `monkey` commands. **PLEASE NOTE:** If you make changes to this file, 
       please run `docker-compose down && docker-compose build` to prevent errors and potential annoyances.
    1. By manually logging into the data container's shell to execute the commands.

    If using approach i, you will just need to run the `init` container by:

        $ docker-compose -f docker-compose.init.yml up -d

    If approach ii, you will need to run the `init` container slightly different to get to a shell:

        $ docker-compose -f docker-compose.yml -f docker-compose.shell.yml up -d data
        $ docker attach $(docker ps -aqf "name=secmonkey-data")
        $ # Run the monkey commands you want to run here, for example:
        $ # monkey add_account_aws --id ACCOUNT_NUM --name ACCOUNT_NAME -r SecurityMonkey

1. Now that the database is setup (and all `monkey` commands run), you can start up the remaining containers (Security Monkey, NGINX, the scheduler, and the workers) via:

        $ docker-compose up -d

1. You can stop the containers with:

        $ docker-compose stop

    Otherwise you can shutdown and clean the images and volumes with:

        $ docker-compose down

Commands:
---------

    $ docker-compose build [postgres | redis | data | api | scheduler | worker | nginx]

    $ docker-compose up -d [postgres | redis | data | api | scheduler | worker | nginx]

    $ docker-compose restart [postgres | redis | data | api | scheduler | worker | nginx]

    $ docker-compose stop

    $ docker-compose down

More Info:
----------

You can get a shell thanks to the `docker-compose.shell.yml` override:

    $ docker-compose -f docker-compose.yml -f docker-compose.shell.yml up -d data
    $ docker attach $(docker ps -aqf "name=secmonkey-data")

This allows you to access Security Monkey's code, and run manual configurations such as:

    $ monkey create_user admin@example.com Admin

and/or:

    $ monkey add_account_aws --id $account --name $name -r SecurityMonkey

This container is useful for local development. It is not required otherwise.

Tips and tricks:
----------------

If you have to restart the scheduler, you don't have to restart all the stack. Just run:

    $ docker-compose restart scheduler

If you want to persist the DB data, create a `postgres-data` directory in the repository root:

    $ mkdir postgres-data

and uncomment these two lines in `docker-compose.yml` (in the `postgres` section):

    #volumes:
    #    - ./postgres-data/:/var/lib/postgresql/data

To monitor an account that requires a credentials file (GCP/OpenStack), uncomment the following in the worker section (and update paths/names):

    #- /path/to/creds.file:/usr/local/src/security_monkey/data/creds.file
