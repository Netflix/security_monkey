"""
.. module: security_monkey.task_scheduler.util
    :platform: Unix
    :synopsis: Instantiates the Celery object for use with task scheduling.

.. version:: $$VERSION$$
.. moduleauthor:: Mike Grima <mgrima@netflix.com>

"""

from celery import Celery
from security_monkey import app
from security_monkey.common.utils import find_modules, load_plugins

import os
import importlib

from security_monkey.exceptions import InvalidCeleryConfigurationType


def get_celery_config_file():
    """This gets the Celery configuration file as a module that Celery uses"""
    return importlib.import_module("security_monkey.{}".format(os.environ.get("SM_CELERY_CONFIG", "celeryconfig")),
                                   "security_monkey")


def make_celery(app):
    """
    Recommended from Flask's documentation to set up the Celery object.
    :param app:
    :return:
    """
    celery = Celery(app.import_name)

    # Determine which Celery configuration to load:
    # The order is:
    # 1. `SM_CELERY_CONFIG` Environment Variable
    # 2. The default "celeryconfig.py"
    celery.config_from_object(get_celery_config_file())
    celery.conf.update(app.config)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def setup():
    """Load the required data for scheduling tasks"""
    find_modules('alerters')
    find_modules('watchers')
    find_modules('auditors')
    load_plugins('security_monkey.plugins')


def get_sm_celery_config_value(celery_config, variable_name, variable_type):
    """
    This returns a celery configuration value of a given type back.

    If it's not set, it will return None.
    :param variable_name: The name of the Celery configuration variable to obtain.
    :param type: The type of the value, such as `list`, `dict`, etc.
    :return:
    """
    try:
        # Directly load the config that Celery is configured to use:
        value = getattr(celery_config, variable_name, None)
        if value is None:
            return

        if not isinstance(value, variable_type):
            raise InvalidCeleryConfigurationType(variable_name, variable_type, type(value))

    except KeyError as _:
        return

    return value


CELERY = make_celery(app)
