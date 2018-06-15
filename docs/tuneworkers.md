ADVANCED: Tuning the Watchers / Prioritizing
=================
By default, Security Monkey watchers as configured in the [Autostarting Doc](autostarting.md) will grab tasks when they are scheduled. If you have many accounts, 
you will need many watchers in order to fetch data in a timely manner. If there are technologies that you are more sensitive about (such as IAM) that you want to 
prioritize, you can do so by spinning up a separate scheduler and watching stack. This section outlines how to do that.

This will require a separate set of scheduler/watchers. This doc outlines a strategy that you can take to accomplish this. 

In this example, we are going to assume that you want to prioritize IAM Roles (called the `iam` stack) vs. all other technologies. 
You will still have a general stack for everything else (called the `main` stack). In this example, the following are required:
1. Dedicated Redis cache for each stack
1. Dedicated scheduler and set of workers for each stack
1. Different scheduler and worker `supervisor` configurations
1. Different `celeryconfig.py` configurations

## Create a dedicated Redis cache for each stack
You will need to have a different Redis cache for each stack. In this example, the `main` stack will have a Redis cache, and the `iam` stack will have a *different* Redis cache.

Create a new Redis cache ([ElastiCache works well](elasticache_directions.md)), and configure it identically to your `main` stack (same security groups and configuration -- only change the name of the Redis instance).
**Keep note of the endpoint, you'll need this later**.

## Create a dedicated Celery configuration
For this use case, you would have two different [Celery configuration Python](https://github.com/Netflix/security_monkey/blob/develop/securitymonkey/celeryconfig.py) files.
You will need to make note of the following section:
```
# This specifies a list of technologies that workers for the above Redis broker should IGNORE.
# This will work on all technologies for enabled accounts that are NOT the technology in the set below:
security_monkey_watcher_ignore = set([])
# ^^ If this is specified, the `security_monkey_only_watch` variable is ignored for this stack.

# This will specify the technologies that workers for the above Redis broker should exclusively watch.
security_monkey_only_watch = set([])
# ^^ If this is specified, the `security_monkey_watcher_ignore` variable is ignored for this stack.
```
In these variables, you will enter in the index name of the technology. For example, `iamrole` for IAM Roles, or `securitygroup` for Security Groups. These are the names
of the technologies as they appear in the UI.

For this use case, we are going to have a dedicated stack of workers (called the `iam` stack) for IAM Roles, and another stack for everything else (called the `main` stack).
1. Make a copy of `security_monkey/celeryconfig.py`, and call it `security_monkey/mainceleryconfig.py`
1. In `security_monkey/mainceleryconfig.py`, make a modification to the `security_monkey_watcher_ignore` variable such that its value is:
    ```
    security_monkey_watcher_ignore = set(['iamrole'])
    ```
1. Save the file.

Next, you will need to make it so that your scheduler and corresponding set of workers that will load this configuration. There is a new environment variable
that Security Monkey will check to properly load this configuration: `SM_CELERY_CONFIG`. For this stack, `SM_CELERY_CONFIG` needs to be set to: `"mainceleryconfig.py"`.
(Do not place `security_monkey` in the variable name...just call it the destination name of the file that resides within the `security_monkey/` python code location -- this is the same place that `manage.py` lives)
Because we utilize `supervisor`, you will need to add this to the `environment` section. Here are sample configurations:

*MAIN-SCHEDULER*
```
[program:securitymonkeyscheduler-main]
user=www-data
autostart=true
autorestart=true
numprocs=1
directory=/usr/local/src/security_monkey/
environment=
    PYTHONPATH='/usr/local/src/security_monkey/',
    PATH="/usr/local/src/security_monkey/venv/bin:%(ENV_PATH)s",
    SM_CELERY_CONFIG="mainceleryconfig.py"
command=/usr/local/src/security_monkey/venv/bin/celery -A security_monkey.task_scheduler.beat.CELERY -s /tmp/sm-celerybeat-schedule --pidfile=/tmp/sm-celerybeat-scheduler.pid beat -l debug

; Causes supervisor to send the termination signal (SIGTERM) to the whole process group.
stopasgroup=true
```

*MAIN-WORKER*
```
[program:securitymonkeyworkers-main]
user=www-data
autostart=true
autorestart=true
numprocs=1
directory=/usr/local/src/security_monkey/
environment=
    PYTHONPATH='/usr/local/src/security_monkey/',
    PATH="/usr/local/src/security_monkey/venv/bin:%(ENV_PATH)s",
    PYTHON_EGG_CACHE='/tmp/python-eggs',
    SM_CELERY_CONFIG="mainceleryconfig.py"
startsecs=60
command=/usr/local/src/security_monkey/venv/bin/celery -A security_monkey.task_scheduler.tasks.CELERY --pidfile=/tmp/sm-celerybeat-worker.pid worker

; Causes supervisor to send the termination signal (SIGTERM) to the whole process group.
stopasgroup=true
```

You will need to place the scheduler `supervisor` config on the scheduler instance, and the worker one on your worker instances. Keep these instances dedicated to
your `main` stack. We'll create another stack for the IAM watchers (per our example).

### Dedicated Stack
With the `main` stack above set to watch everything except for IAM roles, we are now going to make a prioritized stack for IAM roles. Like above, you need to: 
1. Make a copy of `celeryconfig.py`, and call it `iamceleryconfig.py`
1. Since a dedicated Redis cache was created for this stack (if you didn't do this, re read the section above about creating a dedicated Redis cache), you will need to update the
   `broker_url` to point to this new Redis cache. **Failure to do this will result in schedulers looping over and over again, because they will step on each other. That is why
   a dedicated stack is required!**
1. In `iamceleryconfig.py`, make a modification to the `security_monkey_only_watch` variable such that its value is:
    ```
    security_monkey_only_watch = set(['iamrole'])
    ```
1. Save the file.

Next, you will need to make it so that there is a scheduler and corresponding set of workers that will load this configuration. Like above, the `SM_CELERY_CONFIG` variable
needs to be set to load this configuration. For this stack, `SM_CELERY_CONFIG` needs to be set to: `"iamceleryconfig.py"`.
Because we utilize `supervisor`, you will need to add this to the `environment` section. Here are sample configurations:

*IAM-SCHEDULER*
```
[program:securitymonkeyscheduler-iam]
user=www-data
autostart=true
autorestart=true
numprocs=1
directory=/usr/local/src/security_monkey/
environment=
    PYTHONPATH='/usr/local/src/security_monkey/',
    PATH="/usr/local/src/security_monkey/venv/bin:%(ENV_PATH)s",
    SM_CELERY_CONFIG="iamceleryconfig.py"
command=/usr/local/src/security_monkey/venv/bin/celery -A security_monkey.task_scheduler.beat.CELERY -s /tmp/sm-celerybeat-iamschedule --pidfile=/tmp/sm-celerybeat-iamscheduler.pid beat -l debug

; Causes supervisor to send the termination signal (SIGTERM) to the whole process group.
stopasgroup=true
```

*IAM-WORKER*
```
[program:securitymonkeyworkers-iam]
user=www-data
autostart=true
autorestart=true
numprocs=1
directory=/usr/local/src/security_monkey/
environment=
    PYTHONPATH='/usr/local/src/security_monkey/',
    PATH="/usr/local/src/security_monkey/venv/bin:%(ENV_PATH)s",
    PYTHON_EGG_CACHE='/tmp/python-eggs',
    SM_CELERY_CONFIG="iamceleryconfig.py"
startsecs=60
command=/usr/local/src/security_monkey/venv/bin/celery -A security_monkey.task_scheduler.tasks.CELERY --pidfile=/tmp/sm-celerybeat-iamworker.pid worker

; Causes supervisor to send the termination signal (SIGTERM) to the whole process group.
stopasgroup=true
```

**IMPORTANT:** Also note the `--pidfile` parameter has a different `pid` file set. If you have multiple schedulers or workers running on 1 instance, then you will
need to specify separate `pid` files -- otherwise the the `celery beat` command will fail. Also, the `-s` parameter is different for the IAM scheduler as well.

You will need to place the scheduler `supervisor` config on the iam-scheduler instance, and the worker one on your iam-worker instances.

At this point, you should be good to go. You can repeat this process for any set of watchers that you want to prioritize.
