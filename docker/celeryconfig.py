"""
.. module: celeryconfig
    :platform: Unix
    :synopsis: Use this file to set up the Celery configuration for task scheduling.

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
# Broker source: Place yours here:
import os

broker_url = 'redis://{}/{}'.format(
    os.getenv('SECURITY_MONKEY_REDIS_HOST', 'redis'),
    os.getenv('SECURITY_MONKEY_REDIS_DB', '0')
)

# List of modules to import when the Celery worker starts.
imports = ('security_monkey.task_scheduler.tasks',)

# How many processes per worker instance?
worker_concurrency = 10

timezone = "UTC"
enable_utc = True

###########################
# IMPORTANT: This helps avoid memory leak issues - do not change this number!
worker_max_tasks_per_child = 1
############################
