"""
.. module: securitymonkey.celeryconfig
    :platform: Unix
    :synopsis: Use this file to set up the Celery configuration for task scheduling.

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""
import os
# CHANGE THE VALUES BELOW THIS LINE AS APPROPRIATE:
# Broker source: Place yours here:

broker_url = 'redis://{}/{}'.format(
    os.getenv('SECURITY_MONKEY_REDIS_HOST', 'localhost'),
    os.getenv('SECURITY_MONKEY_REDIS_DB', '0')
)

# How many processes per worker instance?
worker_concurrency = 10

# Schedule tasks at full hour or scheduler boot up time
schedule_at_full_hour = False

# Running dedicated stacks? If you want to have dedicated stacks to watch specific technologies (or ignore them)
# for added priority, then set the two variables below:

# This specifies a list of technologies that workers for the above Redis broker should IGNORE.
# This will work on all technologies for enabled accounts that are NOT the technology in the set below:
security_monkey_watcher_ignore = set([])
# ^^ If this is specified, the `security_monkey_only_watch` variable is ignored for this stack.

# This will specify the technologies that workers for the above Redis broker should exclusively watch.
security_monkey_only_watch = set([])
# ^^ If this is specified, the `security_monkey_watcher_ignore` variable is ignored for this stack.
#################

# DO NOT TOUCH ANYTHING BELOW THIS LINE:
timezone = "UTC"
enable_utc = True
imports = ('security_monkey.task_scheduler.tasks',)

###########################
# IMPORTANT: This helps avoid memory leak issues - do not change this number!
worker_max_tasks_per_child = 1
############################
