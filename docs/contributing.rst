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
  Set the environment variable in your current session that tells Flask where the conifguration file is located.::

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

    psql -d postgres
    CREATE DATABASE "securitymonkeydb";
    CREATE ROLE "securitymonkeyuser" LOGIN PASSWORD 'securitymonkeypass';
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

Launch Dart Editor
  Download the Dartlang and Editor from ( http://www.dartlang.org/ )

  Edit dart/lib/util/constants.dart and set API_HOST to this value::

    final String API_HOST = 'http://127.0.0.1:5000/api/1';

  In the Dart Editor, right click on dart/web/ui.html and select "Run in Dartium" from the dropdown menu.

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

    python manage.py find_elb_changes all
    python manage.py find_iamrole_changes all
    python manage.py find_iamgroup_changes "My Test Account"

  You can run the auditors against the items currently in the database::

    python manage.py audit_rds --accounts=all --send_report=False


Development Setup Ubuntu
========================

Apt-get Installs
  These must be installed first.::

    sudo apt-get install git git-flow python-pip postgresql postgresql-contrib libpq-dev python-dev

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
    GRANT Usage, Create ON SCHEMA "securitymonkeydb" TO "securitymonkeyuser";
    set timezone TO 'GMT';

Init DB:
  Run Alembic/FlaskMigrate to create all the database tables.::

    python manage.py db upgrade

Start the API:
  This starts the REST API that the Angular application will communicate with.::

    python manage.py runserver

Launch Dart Editor
  Download the Dartlang and Editor from ( http://www.dartlang.org/ )

  Edit dart/lib/util/constants.dart and set API_HOST to this value::

    final String API_HOST = 'http://127.0.0.1:5000/api/1';

  In the Dart Editor, right click on dart/web/ui.html and select "Run in Dartium" from the dropdown menu.

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

- `Issue tracker <https://github.com/netflix/securitymonkey/issues>`_

- `GitHub documentation <https://help.github.com/>`_
