************
Development Setup on Mac OS X
************

Please follow the instructions below for setting up the Security Monkey development environment on Mac OS X.


Instructions
======================

Install Brew (http://brew.sh)
  Requirement - Xcode Command Line Tools (Popup - Just click Install)::

    ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"

Install Pip
  A tool for installing and managing Python packages::

      sudo easy_install pip

Virtualenv
  A tool to create isolated Python environments::

    sudo pip install virtualenv

VirtualenvWrapper
  virtualenvwrapper is a set of extensions to Ian Bicking’s virtualenv tool. The extensions include wrappers for creating and deleting virtual environments and otherwise managing your development workflow, making it easier to work on more than one project at a time without introducing conflicts in their dependencies. ::

    sudo pip install virtualenvwrapper

Configure VirtualEnvWrapper
  Configure VirtualEnvWrapper so it knows where to store the virtualenvs and where the virtualenvwerapper script is located. ::

    cd ~
    mkdir virtual_envs
    vi ~/.bash_profile

  Add these two lines to your ~/.bash_profile::

    export WORKON_HOME="$HOME/virtual_envs/"
    source "/usr/local/bin/virtualenvwrapper.sh"

  You'll need to open a new terminal (or run ``source ~/.bash_profile``) before you can create the virtualenv::

    mkvirtualenv security_monkey
    workon security_monkey

Clone
  Clone the security monkey code repository. ::

    git clone https://github.com/Netflix/security_monkey.git
    cd security_monkey

SECURITY_MONKEY_SETTINGS
  Set the environment variable in your current session that tells Flask where the configuration file is located. ::

    export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-local.py

  Note - I like to append this to the virtualenv activate script::

    vi $HOME/virtual_envs/security_monkey/bin/activate
    export SECURITY_MONKEY_SETTINGS=$HOME/security_monkey/env-config/config-local.py

Postgres
  Install Postgres.  Create a database for security monkey and add a role.  Set the timezone to GMT. ::

    brew install postgresql

  Start the DB in a new shell::

    postgres -D /usr/local/var/postgres

  Create the database and users and set the timezone. ::

    psql -d postgres -h localhost
    CREATE DATABASE "securitymonkeydb";
    CREATE ROLE "securitymonkeyuser" LOGIN PASSWORD 'securitymonkeypass';
    CREATE SCHEMA securitymonkeydb
    GRANT Usage, Create ON SCHEMA "securitymonkeydb" TO "securitymonkeyuser";
    set timezone to 'GMT';
    select now();

  Exit the Postgres CLI tool::

    CTRL-D

Install Pip Requirements
  Pip will install all the dependencies into the current virtualenv. ::

    pip install -r requirements.txt

Init DB:
  Run Alembic/FlaskMigrate to create all the database tables. ::

    python manage.py db upgrade

Start the API:
  This starts the REST API that the Angular application will communicate with. ::

    python manage.py runserver

Launch and Configure the WebStorm Editor:
  We prefer the WebStorm IDE for developing with Dart: https://www.jetbrains.com/webstorm/

  In addition to WebStorm, you will also need to have the Dart SDK installed.  Please download and install the Dart suite (SDK and Dartium) via brew: ::
  
    $ brew tap dart-lang/dart
    $ brew install dart --with-content-shell --with-dartium

  **Pro-Tip:** During the Dart installation, make note of the Dart SDK Path, and the Dartium path, as this will be used later during the WebStorm Dart plugin configuration. 
  
  For WebStorm to be useful, it will need to have the Dart plugin installed.  You can verify that it is installed by going to WebStorm preferences > Plugins, and searching for "Dart".  If it is checked off, then you have it installed.  If not, then check the box to install it, and click OK.

  At this point, you can import the Security Monkey project into WebStorm.  Please reference the WebStorm documentation for details on importing projects.

  The Dart plugin needs to be configured to utilize the Dart SDK. To configure the Dart plugin, open WebStorm preferences > Languages & Frameworks > Dart.  If it is not already checked, check "Enable Dart Support for the project ...", and paste in the paths for the Dart SDK path Dartium.
  
  - As an example, for a typical Dart OS X installation (via ``brew``), the Dart path will be at: ``/usr/local/opt/dart/libexec``, and the Dartium path will be: ``/usr/local/opt/dart/Chromium.app``

  Once the Dart plugin is configured, you will need to alter a line of Dart code so that Security Monkey can be loaded in your development environment.  You will need to edit the ``dart/lib/util/constants.dart`` file: 

  - Comment out the ``API_HOST`` variable under the ``// Same Box`` section, and uncomment the ``API_HOST`` variable under the ``// LOCAL DEV`` section.

Launch Dartium from within WebStorm:
  From within the Security Monkey project in WebStorm, we will launch the UI (inside the Dartium app).

  To do this, within the Project Viewer/Explorer, right-click on the ``dart/web/ui.html`` file, and select "Open in Browser" > Dartium.

  This will open the Dartium browser with the Security Monkey web UI.

  - **Note:** If you get a ``502: Bad Gateway``, try refreshing the page a few times.

Register a user
  Chromium/Dartium will launch and will redirect to the login page.  Select the Register link ( http://127.0.0.1/register ) to create an account.

Setup an account
  After you have registered an account, proceed to login ( http://127.0.0.1/login ).  Once logged in, click on Settings and on the *+* to add a new account.

Obtaining instance credentials
  You'll need to obtain AWS credentials to execute the watchers.  See the boto documentation for more information.

  http://boto.readthedocs.org/en/latest/boto_config_tut.html

Manually Run the Watchers
  Run the watchers to put some data in the database. ::

    cd ~/security_monkey/
    python manage.py run_change_reporter all

  You can also run an individual watcher::

    python manage.py find_changes -a all -m all
    python manage.py find_changes -a all -m iamrole
    python manage.py find_changes -a "My Test Account" -m iamgroup

  You can run the auditors against the items currently in the database::

    python manage.py audit_changes -a all -m redshift --send_report=False

Next Steps
========================

Continue reading the `Contributing <https://github.com/Netflix/security_monkey/blob/master/docs/contributing.rst>`_ guide for additional instructions.

