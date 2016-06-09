============
Options
============

Security Monkey's behavior can be adjusted with options passed using a configuration
file or directly using the command line. Some parameters are only available
in the configuration file.

If an option is not passed, Security Monkey will use the default value from the file
security_monkey/default-config.py.

You also have the option of providing environment aware configurations through the use
of the SECURITY_MONKEY_SETTINGS environmental variable.

Any variables set via this variable will override the default values specified in default-config.py


Config File
===========

LOG_LEVEL
---------

Standard python logging levels (ERROR, WARNING, DEBUG) depending on how much output you would like to see in your logs.

LOG_FILE
--------

If set, specifies a file to which Security Monkey will write logs. If unset, Security Monkey will log to stderr.

LOG_CFG
-------
Can be used instead of LOG_LEVEL and LOG_FILE.  Should be set to a PEP-0391 compatible logging configuration.  Example::

        LOG_CFG = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s %(levelname)s: %(message)s '
                        '[in %(pathname)s:%(lineno)d]'
                }
            },
            'handlers': {
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'filename': '/var/log/security_monkey/securitymonkey.log',
                    'maxBytes': 10485760,
                    'backupCount': 100,
                    'encoding': 'utf8'
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'security_monkey': {
                    'handlers': ['file', 'console'],
                    'level': 'DEBUG'
                },
                'apscheduler': {
                    'handlers': ['file', 'console'],
                    'level': 'INFO'
                }
            }
        }

R53
---

Specify if you want Security Monkey to create a DNS entry for itself and what DNS name you would like

FQDN
----

This is used for various redirection magic that to get the Security Monkey UI working nice with the API


SQLALCHEMY_DATABASE_URI
-----------------------

Specify where you would like Security Monkey to store it's results

SQLALCHEMY_POOL_SIZE & SQLALCHEMY_MAX_OVERFLOW
----------------------------------------------

Because of the parallel nature of Security Monkey we have to have the ability to tweak the number of concurrent connections we can make. The default values should be sufficient for <= 20 accounts. This may need to be increased if you are dealing with a greater number of accounts.

API_PORT
-------- 

Needed for CORS whitelisting -- this should match the port you have told Security Monkey to listen on. If you are using nginx it should match the port that nginx is listening on for the /api endpoint.

WEB_PORT
--------

Needed for CORS whitelisting -- this should match the port you have configured nginx to listen on for static content.

WEB_PATH
--------


Additional Options
------------------

As Security Monkey uses Flask-Security for authentication see .. _Flask-Security: https://pythonhosted.org/Flask-Security/configuration.html for additional configuration options.


Command line
==================

--host and --port
-------------------

The host and port on which to listen for incoming request. Usually 127.0.0.1
and 8000 to listen locally or 0.0.0.0 and 80 to listen from the outside.

Default: 127.0.0.1 and 8000

Setting file : HOST and PORT

--version and --help
--------------------

Display the help or the version of 0bin.

Default: None

Configuration file equivalent: None

