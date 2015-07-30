************
Contributing
************

Contributions to Security Monkey are welcome! Here are some tips to get you started
hacking on Security Monkey and contributing back your patches.


Development Setup OS X
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
  virtualenvwrapper is a set of extensions to Ian Bicking’s virtualenv tool. The extensions include wrappers for creating and deleting virtual environments and otherwise managing your development workflow, making it easier to work on more than one project at a time without introducing conflicts in their dependencies.::

    sudo pip install virtualenvwrapper

Configure VirtualEnvWrapper
  Configure VirtualEnvWrapper so it knows where to store the virtualenvs and where the virtualenvwerapper script is located.::

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
  Clone the security monkey code repository.::

    git clone https://github.com/Netflix/security_monkey.git
    cd security_monkey

SECURITY_MONKEY_SETTINGS
  Set the environment variable in your current session that tells Flask where the configuration file is located.::

    export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-local.py

  Note - I like to append this to the virtualenv activate script::

    vi $HOME/virtual_envs/security_monkey/bin/activate
    export SECURITY_MONKEY_SETTINGS=$HOME/security_monkey/env-config/config-local.py

Postgres
  Install Postgres.  Create a database for security monkey and add a role.  Set the timezone to GMT.::

    brew install postgresql

  Start the DB in a new shell::

    postgres -D /usr/local/var/postgres

  Create the database and users and set the timezone.::

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
  Pip will install all the dependencies into the current virtualenv.::

    pip install -r requirements.txt

Init DB:
  Run Alembic/FlaskMigrate to create all the database tables.::

    python manage.py db upgrade

Start the API:
  This starts the REST API that the Angular application will communicate with.::

    python manage.py runserver
    

Launch and Configure the WebStorm Editor:
  We prefer the WebStorm IDE for developing with Dart: https://www.jetbrains.com/webstorm/

  In addition to WebStorm, you will also need to have the Dart SDK installed.  Please download and install the Dart SDK from: http://www.dartlang.org/download, and follow the installation instructions.

  **Pro-Tip:** During the Dart installation, make note of the Dart SDK Path, and the Dartium path, as this will be used later during the WebStorm configuration. 
  
  For WebStorm to be useful, it will need to have the Dart plugin installed.  You can verify that it is installed by going to the WebStorm preferences > Plugins, and searching for "Dart".  If it is checked off, then you have it installed.  If not, then check the box to install it, and click OK.

  The Dart plugin needs to be configured to utilize the Dart SDK.  The two paths mentioned in the Pro-Tip above will be used here.  To set the Dart SDK, open the WebStorm preferences > Languages & Frameworks > Dart, and paste in the Dart SDK path and the Dartium path.
  
  - As an example, for a typical Dart OS X installation (via brew), the Dart path will be at: ``/usr/local/opt/dart/libexec``, and the Dartium path will be: ``/usr/local/opt/dart/Chromium.app``

  At this point, import the Security Monkey project into WebStorm.  Once imported, you will need to edit the ``dart/lib/util/constants.dart`` file to prepare it for for local development: 

  - Comment out the ``API_HOST`` variable under the ``// Same Box`` section, and uncomment the ``API_HOST`` variable under the ``// LOCAL DEV`` section.

Launch Dartium from within WebStorm:
  From within the Security Monkey project in WebStorm, we will launch the UI (inside the Dartium app).

  To do this, within the Project viewer/explorer, right-click on the ``dart/web/ui.html`` file, and select "Open in Browser" > Dartium.

  This will open the Dartium browser with the Security Monkey web UI.

Register a user
  Chromium/Dartium will launch and will redirect to the login page.  Select the Register link ( http://127.0.0.1/register ) to create an account.

Setup an account
  After you have registered an account, proceed to login ( http://127.0.0.1/login ).  Once logged in, click on Settings and on the *+* to add a new account.

Obtaining instance credentials
  You'll need to obtain AWS credentials to execute the watchers.  See the boto documentation for more information.

  http://boto.readthedocs.org/en/latest/boto_config_tut.html

Manually Run the Watchers
  Run the watchers to put some data in the database.::

    cd ~/security_monkey/
    python manage.py run_change_reporter all

  You can also run an individual watcher::

    python manage.py find_changes -a all -m all
    python manage.py find_changes -a all -m iamrole
    python manage.py find_changes -a "My Test Account" -m iamgroup

  You can run the auditors against the items currently in the database::

    python manage.py audit_changes -a all -m redshift --send_report=False


Development Setup Ubuntu
========================

Apt-get Installs
  These must be installed first.::

    sudo apt-get install git git-flow python-pip postgresql postgresql-contrib libpq-dev python-dev swig

Install Virtualenv
  A tool to create isolated Python environments::

    sudo pip install virtualenv

  Create a folder to hold your virtualenvs::

    cd ~
    mkdir virtual_envs
    cd virtual_envs

  Create a virtualenv for security_monkey::

    virtualenv security_monkey

  Activate the security_monkey virtualenv::

    source ~/virtual_envs/security_monkey/bin/activate

Clone the repository
  Clone the security monkey code repository.::

    cd ~
    git clone https://github.com/Netflix/security_monkey.git
    cd security_monkey

Install Pip Requirements
  Pip will install all the dependencies into the current virtualenv.::

    pip install -r requirements.txt

SECURITY_MONKEY_SETTINGS
  Set the environment variable in your current session that tells Flask where the conifguration file is located.::

    export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-local.py
    # Note - I like to append this to the virtualenv activate script
    vi $HOME/virtual_envs/security_monkey/bin/activate
    export SECURITY_MONKEY_SETTINGS=$HOME/security_monkey/env-config/config-local.py

Postgres
  Install Postgres.  Create a database for security monkey and add a role.  Set the timezone to GMT.::

    sudo -u postgres psql
    CREATE DATABASE "securitymonkeydb";
    CREATE ROLE "securitymonkeyuser" LOGIN PASSWORD 'securitymonkeypass';
    CREATE SCHEMA securitymonkeydb
    GRANT Usage, Create ON SCHEMA "securitymonkeydb" TO "securitymonkeyuser";
    set timezone TO 'GMT';
    select now();
    \q

Init DB:
  Run Alembic/FlaskMigrate to create all the database tables.::

    python manage.py db upgrade

Start the API:
  This starts the REST API that the Angular application will communicate with.::

    python manage.py runserver

Launch and Configure the WebStorm Editor:
  We prefer the WebStorm IDE for developing with Dart: https://www.jetbrains.com/webstorm/

  In addition to WebStorm, you will also need to have the Dart SDK installed.  Please download and install the Dart SDK from: http://www.dartlang.org/download, and follow the installation instructions. 

  **Note:** You will need to install Dartium as well.  This requires extra steps and is unfortunately not available as a Debian package.  Dartium is packaged as a .zip file in the section "Installing from a zip file" on the Dart download page.  Download the Dartium zip file, and follow the following instructions:

  1.) Extract the .zip file
  
  2.) Run the following commands. ::

    sudo cp -R /path/to/your/extracted/Dartium/zip/file /opt/Dartium
    sudo chmod 755 /opt/Dartium
    cd /opt/Dartium
    sudo find ./ -type d -exec chmod 755 {} \;
    sudo find ./ -type f -exec chmod 644 {} \;
    sudo chmod +x chrome
    sudo ln -s /lib/x86_64-linux-gnu/libudev.so.1 /lib/x86_64-linux-gnu/libudev.so.0

  For WebStorm to be useful, it will need to have the Dart plugin installed.  You can verify that it is installed by going to WebStorm preferences > Plugins, and searching for "Dart".  If it is checked off, then you have it installed.  If not, then check the box to install it, and click OK.

  Import the Security Monkey project into WebStorm.

  The Dart plugin needs to be configured to utilize the Dart SDK. To set the Dart SDK, open the WebStorm preferences > Languages & Frameworks > Dart.  If it is not already checked, check "Enable Dart Support for the project ...", and paste in the paths for the Dart SDK path Dartium.
  
  - As an example, for a typical Dart Ubuntu installation (via apt-get), the Dart path will be at: ``/usr/lib/dart``, and the Dartium path (following the instructions above) will be: ``/opt/Dartium/chrome``

  At this point, you will need to alter a line of Dart code so that Security Monkey can be loaded in your development environment.  You will need to edit the ``dart/lib/util/constants.dart`` file: 

  - Comment out the ``API_HOST`` variable under the ``// Same Box`` section, and uncomment the ``API_HOST`` variable under the ``// LOCAL DEV`` section.

Launch Dartium from within WebStorm:
  From within the Security Monkey project in WebStorm, we will launch the UI (inside the Dartium app).

  To do this, within the Project viewer/explorer, right-click on the ``dart/web/ui.html`` file, and select "Open in Browser" > Dartium.

  This will open the Dartium browser with the Security Monkey web UI.  

  - **Note:** If you get a ``502: Bad Gateway``, try refreshing the page a few times.

Register a user
  Chromium/Dartium will launch and will redirect to the login page.  Select the Register link ( http://127.0.0.1/register ) to create an account.

Setup an account
  After you have registered an account, proceed to login ( http://127.0.0.1/login ).  Once logged in, click on Settings and on the *+* to add a new account.

More
  Read the OS X sections on ``Obtaining instance credentials`` and how to ``Manually Run the Watchers``.

Submitting changes
==================

- Code should be accompanied by tests and documentation. Maintain our excellent
  test coverage.

- Follow the existing code style, especially make sure ``flake8`` does not
  complain about anything.

- Write good commit messages. Here's three blog posts on how to do it right:

  - `Writing Git commit messages
    <http://365git.tumblr.com/post/3308646748/writing-git-commit-messages>`_

  - `A Note About Git Commit Messages
    <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_

  - `On commit messages
    <http://who-t.blogspot.ch/2009/12/on-commit-messages.html>`_

- One branch per feature or fix. Keep branches small and on topic.

- Send a pull request to the ``v1/develop`` branch. See the `GitHub pull
  request docs <https://help.github.com/articles/using-pull-requests>`_ for
  help.


Additional resources
====================

- `Issue tracker <https://github.com/netflix/security_monkey/issues>`_

- `GitHub documentation <https://help.github.com/>`_
