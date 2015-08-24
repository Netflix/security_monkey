************
Contributing
************

Contributions to Security Monkey are welcome! Here are some tips to get you started
hacking on Security Monkey and contributing back your patches.


Development Setup OS X
======================

Please review the `Mac OS X Development Setup Instructions <dev_setup_osx.rst>`_ to set up your Mac for Security Monkey development. 


Development Setup Ubuntu
========================

Apt-get Installs
  These must be installed first. ::

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
  Clone the security monkey code repository. ::

    cd ~
    git clone https://github.com/Netflix/security_monkey.git
    cd security_monkey

Install Pip Requirements
  Pip will install all the dependencies into the current virtualenv. ::

    pip install -r requirements.txt

SECURITY_MONKEY_SETTINGS
  Set the environment variable in your current session that tells Flask where the conifguration file is located. ::

    export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-local.py
    # Note - I like to append this to the virtualenv activate script
    vi $HOME/virtual_envs/security_monkey/bin/activate
    export SECURITY_MONKEY_SETTINGS=$HOME/security_monkey/env-config/config-local.py

Postgres
  Install Postgres.  Create a database for security monkey and add a role.  Set the timezone to GMT. ::

    sudo -u postgres psql
    CREATE DATABASE "securitymonkeydb";
    CREATE ROLE "securitymonkeyuser" LOGIN PASSWORD 'securitymonkeypass';
    CREATE SCHEMA securitymonkeydb
    GRANT Usage, Create ON SCHEMA "securitymonkeydb" TO "securitymonkeyuser";
    set timezone TO 'GMT';
    select now();
    \q

Init DB:
  Run Alembic/FlaskMigrate to create all the database tables. ::

    python manage.py db upgrade

Start the API:
  This starts the REST API that the Angular application will communicate with. ::

    python manage.py runserver

Launch and Configure the WebStorm Editor:
  We prefer the WebStorm IDE for developing with Dart: https://www.jetbrains.com/webstorm/

  In addition to WebStorm, you will also need to have the Dart SDK installed.  Please download and install the Dart SDK from: https://www.dartlang.org/downloads/linux.html, and follow the installation instructions. 

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

  At this point, you can import the Security Monkey project into WebStorm.  Please reference the WebStorm documentation for details on importing projects.

  The Dart plugin needs to be configured to utilize the Dart SDK. To configure the Dart plugin, open WebStorm preferences > Languages & Frameworks > Dart.  If it is not already checked, check "Enable Dart Support for the project ...", and paste in the paths for the Dart SDK path Dartium.
  
  - As an example, for a typical Dart Ubuntu installation (via ``apt-get``), the Dart path will be at: ``/usr/lib/dart``, and the Dartium path (following the instructions above) will be: ``/opt/Dartium/chrome``

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
