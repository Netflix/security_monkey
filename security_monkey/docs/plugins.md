Plugins
=======

Security Monkey can be extended by writing own Account Managers, Watchers and Auditors. To do this you need to create a subclass of either `security_monkey.account_manager.AccountManager`, `security_monkey.watcher.Watcher` or `security_monkey.auditor.Auditor`.

To make extension available to Security Monkey it should have entry point under group `security_monkey.plugins`.

Sample AccountManager plugin
----------------------------

Assume we have a file account.py in directory my\_sm\_plugins/my\_sm\_plugins/account.py:

~~~~ {.sourceCode .python}
from security_monkey.account_manager import AccountManager

class MyAccountManager(AccountManager):
    pass
~~~~

NOTE: there also shoule be file my\_sm\_plugins/my\_sm\_plugins/\_\_init\_\_.py

And we have a file setup.py in directory my\_sm\_plugins:

~~~~ {.sourceCode .python}
from setuptools import setup, find_packages

setup(
    name="my_sm_plugins",
    version="0.1-dev0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["security_monkey"],
    entry_points={
        "security_monkey.plugins": [
            "my_sm_plugins.account = my_sm_plugins.account",
        ]
    }
)
~~~~

Then we can install `my_sm_plugins` package and have security\_monkey with our plugin available.
