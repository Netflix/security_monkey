Development Setup on Windows
============================

Please follow the instructions below for setting up the Security Monkey development environment on Windows 10.

These instructions were created after consulting my install notes after recently getting a Windows 10 machine. If you're a Powershell guru, please feel free to send a PR to fix any errors.

Windows Development
-------------------

I'm pretty happy with development on Windows. Docker seems much easier to work with (No need for virtualbox). Gunicorn does not yet support Windows (Issue \#524). Luckily, we don't need Gunicorn for local dev. Powershell is a worthy command line environment. If all else fails, use WSL (Windows Subsystem for Linux).

AWS Credentials
---------------

You will need to have the proper IAM Role configuration in place. See [IAM Role Setup on AWS](iam_aws.md) for more details. Additionally, you will need to have IAM keys available within your environment variables. There are many ways to accomplish this. Please see Amazon's documentation for additional details: <http://docs.aws.amazon.com/general/latest/gr/getting-aws-sec-creds.html>.

Additionally, see the boto documentation for more information: <http://boto.readthedocs.org/en/latest/boto_config_tut.html>

Install Chocolatey
------------------

Follow the instructions to install Chocolatey:

<https://chocolatey.org/install>

Install Python
--------------

Install python 2.7 with Chocolatey.:

    choco install python2

Setup Powershell
----------------

The following steps are a summary of the steps at <http://www.tylerbutler.com/2012/05/how-to-install-python-pip-and-virtualenv-on-windows-with-powershell/>

### Execution Policy

You'll need to set the execution policy. There are a few options described at <https://technet.microsoft.com/en-us/library/ee176961.aspx>

You'll need to run something like this:

    Set-ExecutionPolicy RemoteSigned

### VirtualEnv

Install virtualenv and virtualenvwrapper from pypi:

    pip install virtualenv
    pip install virtualenvwrapper-powershell

Try to import the powershell module:

    Import-Module virtualenvwrapper

At this point you may receive the following error:

    Get-Content : Cannot find path 'Function:\TabExpansion' because it does not exist.

You'll need to find and edit the file virtualenvwrapperTabExpansion.psm1. On line 12, replace Get-Content Function:TabExpansion with Get-Content Function:TabExpansion2. This should fix the import error.

If the \~/.virtualenvs folder wasn't created, do that now:

    mkdir ~/.virtualenvs

### Automatically import the virtualenvwrapper module on powershell startup.

In bash, you would typically edit your \~/.bashrc to load modules and setup your environment. On Powershell, you'll use \$profile. Powershell has a few different \$profiles you can use. You can see them all with this command:

    $profile | Format-List * -Force
    AllUsersAllHosts       : C:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
    AllUsersCurrentHost    : C:\Windows\System32\WindowsPowerShell\v1.0\Microsoft.PowerShell_profile.ps1
    CurrentUserAllHosts    : C:\Users\<youruser>\Documents\WindowsPowerShell\profile.ps1
    CurrentUserCurrentHost : C:\Users\<youruser>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
    Length                 : 77

If you're not sure, we're going to use CurrentUserAllHosts. If the file doesn't already exist, we can easily create it:

    New-Item -Path $Profile.CurrentUserAllHosts -Type file -Force

Now open it with a text editor and add this line:

    Import-Module virtualenvwrapper

All new powershell windows should have this module.:

    Get-Command *virtualenv*

Clone the Codebase
------------------

Navigate to wherever you like to mash on code and clone the repository. We'll use \~\\Github here.:

    cd ~
    mkdir Github
    cd Github

If you don't already have git installed:

    choco install git

Clone security\_monkey:

    git clone git@github.com:Netflix/security_monkey.git

Create a security\_monkey virtualenv
------------------------------------

You can use the powershell syntax:

    New-VirtualEnvironment security_monkey

Or use the aliased commands you're probably more familiar with:

    mkvirtualenv security_monkey

Before we attempt to install setup.py, let's grab a couple modules from pypi so we don't need to compile them.:

    pip install cryptography
    pip install bcrypt

### Install psycopg2

This part seems a bit yucky. Let me know if you find a cleaner way.

-   Go to <http://www.stickpeople.com/projects/python/win-psycopg/>
-   Download the exe for your python version and processor architecture. I'll continue with psycopg2-2.6.2.win-amd64-py2.7-pg9.5.3-release.exe
-   In powershell, ensure your virtualenv is activated and install the exe:

        workon security_monkey
        easy_install psycopg2-2.6.2.win-amd64-py2.7-pg9.5.3-release.exe

### Setting SECURITY\_MONKEY\_SETTINGS

You can set the SECURITY_MONKEY_SETTINGS environment variable if you would like security_monkey to use a config file other than `env-config/config.py`.  It may be a good idea to create a `config-local.py` and use that instead.

You set powershell environment variables with `$env:`

    $env:SECURITY_MONKEY_SETTINGS = "C:\Users\<youruser>\...\GitHub\security_monkey\env-config\config-local.py"

It might be a good idea to drop this into your `$profile` as well...

Install Setup.py
----------------

With your virtualenv activated, this will install the security\_monkey python module for dev::

    cd \~/Github/security\_monkey/
    workon security\_monkey
    python setup.py develop

We should be able to run manage.py to see usage information:

    monkey

### Setup a development DB

Instead of installing postgres, let's use docker for the DB. Windows has good docker support. You should be able to use Chocolatey, but I downloaded it directly from their website.:

    choco install docker

I actually downloaded the stable branch from here: <https://docs.docker.com/docker-for-windows/>

Once you have docker, pull a postgres container down. I'm using this one: <https://hub.docker.com/r/library/postgres/> You should be able to start it with this command:

    docker run --name some-postgres

Kitematic is a nice UI tool for managing running containers. You can use it to set the postgres container to be reachable from localhost on 5432 and to set environment variables which the container uses to set the database name, username, password, etc.

If you leave the DB paramaters at their default, you'll need to modify config-local.py:

    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:mysecretpassword@localhost:5432/postgres'

Install the security\_monkey DB tables:

    monkey db upgrade

FYI - Navicat is a great tool for exploring the DB.

Add Amazon Accounts
-------------------

This will add Amazon owned AWS accounts to security monkey. :

    monkey amazon_accounts

Add a user account
------------------

This will add a user account that can be used later to login to the web ui:

    monkey create\_user <email@youremail.com> Admin

The first argument is the email address of the new user. The second parameter is the role and must be one of [anonymous, View, Comment, Justify, Admin].

Start the Security Monkey API
-----------------------------

This starts the REST API that the Angular application will communicate with. :

    monkey runserver

### Dart Development

Install the dart SDK:

    choco install dart-sdk

This will install a few tools in C:tools. Let's install webstorm and configure it to use the dart-sdk:

    choco install webstorm

Open Webstorm and select the \~/Github/security\_monkey/dart folder to open. We need webstorm to install the dart package. I believe it will popup and ask to install the dart package if you open the pubspec.yaml, or one of the dart files. Once the dart package is installed, go to File-\>Settings and select dart from the left column.

-   Check the box Enable Dart Support ... and provide the path C:\\tools\\dart-sdk
-   Provide the path to dartium: C:\\tools\\dartium\\chrome.exe

Before we instruct webstorm to open ui.html with Dartium, we'll need to update \`dart/lib/util/constants.dart\`:

    library security_monkey.constants;
    ...
    // LOCAL DEV
    final String API_HOST = 'http://127.0.0.1:5000/api/1';
    //final bool REMOTE_AUTH = true;

    // Same Box
    //final String API_HOST = '/api/1';
    final bool REMOTE_AUTH = false;

You should now be able to use webstorm and dartium to work on the web ui.

TODO: Determine if it makes sense to modify security\_monkey/\_\_init\_\_.py to change the static\_url path to the dart folder for webstorm development:

    app = Flask(__name__, static_url_path='../dart/')
    # does this work?

Log into Security Monkey
------------------------

Logging into Security Monkey is done by accessing the login page: `http://127.0.0.1:8080/login`. Please note, that in the development environment, when you log in, you will be redirected to `http://127.0.0.1/None`. This only occurs in the development environment. You will need to navigate to the WebStorm address and port (you can simply use WebStorm to re-open the page in Daritum). Once you are back in Dartium, you will be greeted with the main Security Monkey interface.

Watch an AWS Account
--------------------

After you have registered a user, logged in, and re-opened Dartium from WebStorm, you should be at the main Security Monkey interface. Once here, click on Settings and on the *+* to add a new AWS account to sync.

Manually Run the Account Watchers
---------------------------------

Run the watchers to put some data in the database. :

    cd ~/Github/security_monkey/
    monkey run_change_reporter all

You can also run an individual watcher:

    monkey find_changes -a all -m all
    monkey find_changes -a all -m iamrole
    monkey find_changes -a "My Test Account" -m iamgroup

You can run the auditors against the items currently in the database:

    monkey audit_changes -a all -m redshift --send_report=False

Next Steps
----------

Continue reading the [Contributing](contributing.md) guide for additional instructions.
