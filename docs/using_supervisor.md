Using supervisor
================

Supervisor is a very nice way to manage you Python processes. We won't cover the setup (which is just apt-get install supervisor or pip install supervisor most of the time), but here is a quick overview on how to use it.

Create a configuration file named security\_monkey.conf under /etc/supervisor/conf.d/:

    # Control Startup/Shutdown:
    # sudo supervisorctl
    
    [program:securitymonkey]
    user=www-data
    autostart=true
    autorestart=true
    environment=PYTHONPATH='/usr/local/src/security_monkey/',PATH="/usr/local/src/security_monkey/venv/bin:%(ENV_PATH)s"
    command=monkey run_api_server
    
    [program:securitymonkeyscheduler]
    user=www-data
    autostart=true
    autorestart=true
    directory=/usr/local/src/security_monkey/
    environment=PYTHONPATH='/usr/local/src/security_monkey/',PATH="/usr/local/src/security_monkey/venv/bin:%(ENV_PATH)s"
    command=monkey start_scheduler

The 3 first entries are just boiler plate to get you started, you can copy them verbatim.

The fourth line enables the `virtualenv` created in /usr/local/src/security_monkey/venv/.

The fifth line defines one process supervisor should manage.

It means it will run the command:

    monkey run_api_server
    
which translates to:

    python security_monkey/manage.py run_api_server

In the directory, with the environment and the user you defined.

This command will be ran as a daemon, in the background.

autostart and autorestart just make it fire and forget: the site will always be running, even it crashes temporarily or if you restart the machine.

Normally run supervisor:

    sudo service supervisor restart

Then you can manage the process by running:

    sudo supervisorctl

It will start a shell from were you can start/stop/restart the service

It's common for supervisor to log to `/var/log/supervisor/` and security_monkey is often configured to log to `/var/log/security_monkey`.