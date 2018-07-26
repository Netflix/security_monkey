import json
import os
import stat

from logging import handlers
from logging.config import dictConfig

# Need to get the location of the env-config/loggingconfig.json file
# Is this an env var?
from security_monkey.utils import resolve_app_config_path

LOG_CFG = os.path.join(os.path.dirname(resolve_app_config_path()), "logconfig.json")


def setup_base_logging():
    """Sets up the base logger for Security Monkey.

    The Flask logger will inherit from this at a minimum.
    :return:
    """
    dictConfig(json.loads(open(LOG_CFG, 'r').read()))


class GroupWriteRotatingFileHandler(handlers.RotatingFileHandler):
    def doRollover(self):
        """Override base class method to make the new log file group writable."""
        # Rotate the file first.
        handlers.RotatingFileHandler.doRollover(self)

        # Add group write to the current permissions.
        try:
            currMode = os.stat(self.baseFilename).st_mode
            os.chmod(self.baseFilename, currMode | stat.S_IWGRP)
        except OSError:
            pass
