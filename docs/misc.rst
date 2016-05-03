==============
Miscellaneous
==============

Force Audit
-----------
Sometimes you will want to force an audit even though there is no configuration 
change in AWS resources.

For instance when you change a whitelist or add a 3rd party account, configuration
will not be audited again until the daily check at 10am.

In this case, you can force an audit by running:

.. code-block:: bash
   
    export SECURITY_MONKEY_SETTINGS=/usr/local/src/security_monkey/env-config/config-deploy.py
    python manage.py audit_changes -m s3

Be sure to set your SECURITY_MONKEY_SETTINGS environment variable first.

For an email by adding ``-r True``:

.. code-block:: bash

    python manage.py audit_changes -m s3 -r True

Valid values for ``audit_changes -m`` are:
 - elb
 - elasticip
 - elasticsearchservice
 - iamrole, iamssl, iamuser, iamgroup
 - keypair
 - policy
 - redshift
 - rds
 - securitygroup
 - ses
 - sns
 - sqs
 - s3
 - vpc
 - subnet
 - routetable

Scheduler Hacking
-----------------

Edit ``security_monkey/scheduler.py`` to change daily check schedule::

    scheduler.add_cron_job(_audit_changes, hour=10, day_of_week="mon-fri", args=[account, auditors, True])

Edit ``security_monkey/watcher.py`` to change check interval from every 15 minutes


