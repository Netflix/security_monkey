
=================
Using supervisor
=================

Supervisor is a very nice way to manage you Python processes. We won't cover
the setup (which is just apt-get install supervisor or pip install supervisor
most of the time), but here is a quick overview on how to use it.

Create a configuration file named supervisor.ini::

    [unix_http_server]
    file=/tmp/supervisor.sock;

    [supervisorctl]
    serverurl=unix:///tmp/supervisor.sock;

    [rpcinterface:supervisor]
    supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface

    [supervisord]
    logfile=/tmp/securitymonkey.log
    logfile_maxbytes=50MB
    logfile_backups=2
    loglevel=trace
    pidfile=/tmp/supervisord.pid
    nodaemon=false
    minfds=1024
    minprocs=200
    user=securitymonkey

    [program:securitymonkey]
    command=python /path/to/security_monkey/manage.py manage.py run_api_server

    [program:securitymonkeyscheduler]
    command=python /path/to/security_monkey/manage.py manage.py scheduler

    directory=/path/to/security_monkey/
    environment=PYTHONPATH='/path/to/security_monkey/'
    user=securitymonkey
    autostart=true
    autorestart=true

The 4 first entries are just boiler plate to get you started, you can copy
them verbatim.

The last one define one (you can have many) process supervisor should manage.

It means it will run the command::

    python manage.py run_api_server


In the directory, with the environment and the user you defined.

This command will be ran as a daemon, in the background.

`autostart` and `autorestart` just make it fire and forget: the site will always be
running, even it crashes temporarily or if you restart the machine.

The first time you run supervisor, pass it the configuration file::

    supervisord -c /path/to/supervisor.ini

Then you can manage the process by running::

    supervisorctl -c /path/to/supervisor.ini

It will start a shell from were you can start/stop/restart the service

You can read all errors that might occurs from /tmp/securitymonkey.log.
