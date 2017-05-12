#!/usr/bin/env bash
set -eo pipefail

# Output python info
/usr/src/venv/bin/python --version
/usr/src/venv/bin/pip --version
/usr/src/venv/bin/easy_install --version

# Install app develop/test packages
/usr/src/venv/bin/python setup.py develop
/usr/src/venv/bin/pip install .[tests]

# Test latest db migration
/usr/src/venv/bin/python manage.py db upgrade
/usr/src/venv/bin/python manage.py db downgrade

# Run application tests
/usr/src/venv/bin/python manage.py db upgrade
/usr/src/venv/bin/py.test -vv -s security_monkey/tests/