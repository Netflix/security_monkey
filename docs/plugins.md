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


Complex plugin
---------------------------

You can add a complete plugins (adding views, everythings, etc ...)
To do that you can add a subfolder in plugins folder

To make security_monkey work with your plugin you have several tasks to do

 - [ ] Make your class inherit from SMPlugin
 - [ ] Define a class field named "index" to register your plugin
 - [ ] Implement 3 abstracts functions
	 - [ ] Implement class method register
The purpose of this method is for your plugin to register itself in the correct data structure
For example is you have new views you will have to register those views in the api, etc.
Check `splunk_alerter/splunk_alerter_plugins.py` for example
	 - [ ] Implement build
This method is here to be call after the plugin get its configuration in `self.config`
In other word you will have to build your intern plugin config structure from `self.config`
	 - [ ] Implement convert_to_json
Basically the configuration of your plugin is not a specific table in the DB for your plugin. Instead each plugin can have a row in the table `SMPluginConfig` with the following :

| ID  | classname | config |
| ------------- | ------------- | ------------- |
| 1 | SplunkAlerterPlugin  | {json_data}
| ## | YourPluginClassName  | {your_config}  |

Since you do that, you can save your current Plugin Config by calling `SMPlugin.save_config("classname")` function

### Installation of Plugins table
To be able to use plugins (if you already have an instance of security monkey running), you have to upgrade your db with flask.
To perform the upgrade you just have to run the following commands

    <in security_monkey root>
    source venv/bin/activate
    monkey db migrate
    # At this point you can rewiew changes in file generate by db migrate in the path return by the command
    # For example its like /usr/local/src/security_monkey/migrations/versions/2db5<hash>_.py
	# When you review changes run "monkey db upgrade" to apply changes
    monkey db upgrade

