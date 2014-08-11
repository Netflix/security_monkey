*************
API Reference
*************

At a high-level, Security Monkey consists of the following components:

Watcher - Component that monitors a given AWS account and technology (e.g. S3, EC2). The
Watcher detects and records changes to configurations. So, if an S3 bucket policy 
changes, the Watcher will detect this and store the change.

Notifier - Component that lets a user or group of users know when a particular item has changed. This component also provides notification based on the triggering of audit rules.

Auditor - Component that executes a set of business rules against an AWS configuration to
determine the level of risk associated with the configuration. For example, a rule may 
look for a security group with a rule allowing ingress from 0.0.0.0/0 (meaning the 
security group is open to the Internet). Or, a rule may look for an S3 policy that 
allows access from an unknown AWS account (meaning you may be unintentionally sharing
the data stored in your S3 bucket). Security Monkey has a number of built-in rules 
included, and users are free to add their own rules. 

.. module:: security_monkey

.. attribute:: __version__
	
	security_monkey's version number in :pep:`386` format.

	::

		>>> import security_monkey
		>>> security_monkey.__version__
		u'0.1.2'


Class and method level definitions and documentation

.. toctree::
    :maxdepth: 2

    security_monkey

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
