************
Development Setup on Mac OS X
************

Please follow the instructions below for setting up the Security Monkey development environment on Mac OS X.

AWS Credentials
==========================
You will need to have the proper IAM Role configuration in place.  See `Configuration <configuration.rst>`_ for more details.  Additionally, you will need to have IAM keys available within your environment variables.  There are many ways to accomplish this.  Please see Amazon's documentation for additional details: http://docs.aws.amazon.com/general/latest/gr/getting-aws-sec-creds.html.
  
Additionally, see the boto documentation for more information: http://boto.readthedocs.org/en/latest/boto_config_tut.html

Install Brew (http://brew.sh)
==========================
Requirement - Xcode Command Line Tools (Popup - Just click Install)::

    ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"

Install Pip
==========================
A tool for installing and managing Python packages::

    sudo easy_install pip

Setup Virtualenv
==========================
Virtualenv is a tool to create isolated Python environments.  You will need to install it::

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

Clone Security Monkey
==========================
Clone the security monkey code repository. ::

    git clone https://github.com/Netflix/security_monkey.git
    cd security_monkey

SECURITY_MONKEY_SETTINGS
  Set the environment variable in your current session that tells Flask where the configuration file is located. ::

    export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-local.py

  Note - I like to append this to the virtualenv activate script::

    vi $HOME/virtual_envs/security_monkey/bin/activate
    export SECURITY_MONKEY_SETTINGS=$HOME/security_monkey/env-config/config-local.py

Install PostgreSQL
==========================
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
==========================
Pip will install all the dependencies into the current virtualenv. ::

    pip install -r requirements.txt

Init the Security Monkey DB
==========================
Run Alembic/FlaskMigrate to create all the database tables. ::

    python manage.py db upgrade

Install and configure NGINX
==========================
NGINX will be used to serve static content for Security Monkey.  Use ``brew`` to install. ::

   brew install nginx  
  
There will be some output about how to start NGINX, and where it's configuration resides. Choose the approach that works best for you. (We personally advise against starting things automatically on boot for your development box)

The NGINX configuration will be located at: ``/usr/local/etc/nginx/``. You will need to make a modification to the nginx.conf file. The configuration changes include the following:

- Disabling port 8080 for the main nginx.conf file
- Importing the Security Monkey specific configuration
  
Open the main NGINX configuration file: ``/usr/local/etc/nginx/nginx.conf``, and in the ``http`` section, add the line ::
  
    include securitymonkey.conf;

Next, comment out the ``listen`` line (under the ``server`` section) ::
  
    server {
      listen       8080;   # Comment out this line by placing a '#' in front of 'listen'
  
Next, you will create the ``securitymonkey.conf`` NGINX configuration file.  Create this file under ``/usr/local/etc/nginx/``, and paste in the following (MAKE NOTE OF SPECIFIC SECTIONS) ::
  
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Frame-Options "SAMEORIGIN";
    add_header Strict-Transport-Security "max-age=631138519";
    add_header Content-Security-Policy "default-src 'self'; font-src 'self' https://fonts.gstatic.com; script-src     'self' https://ajax.googleapis.com; style-src 'self' https://fonts.googleapis.com;";
    
    server {
     listen      0.0.0.0:8080;
   
     # EDIT THIS TO YOUR DEVELOPMENT PATH HERE:
     access_log          /PATH/TO/YOUR/CLONED/SECURITY_MONKEY_BASE_DIR/devlog/security_monkey.access.log;
     error_log           /PATH/TO/YOUR/CLONED/SECURITY_MONKEY_BASE_DIR/devlog/security_monkey.error.log;
     
     location ~* ^/(reset|confirm|healthcheck|register|login|logout|api) {
          proxy_read_timeout 120;
          proxy_pass  http://127.0.0.1:5000;
          proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
          proxy_redirect off;
          proxy_buffering off;
          proxy_set_header        Host            $host;
          proxy_set_header        X-Real-IP       $remote_addr;
          proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
      }
      
      location /static {
          rewrite ^/static/(.*)$ /$1 break;
          # EDIT THIS TO YOUR DEVELOPMENT PATH HERE:
          root /PATH/TO/YOUR/CLONED/SECURITY_MONKEY_BASE_DIR/dart/web;
          index ui.html;
      }
      
      location / {
          # EDIT THIS TO YOUR DEVELOPMENT PATH HERE:
          root /PATH/TO/YOUR/CLONED/SECURITY_MONKEY_BASE_DIR/dart/web;
          index ui.html;
      }
    }

NGINX can be started by running the ``nginx`` command in the Terminal.  You will need to run ``nginx`` before moving on.  This will also output any errors that are encountered when reading the configuration files.

Launch and Configure the WebStorm Editor
==========================
We prefer the WebStorm IDE for developing with Dart: https://www.jetbrains.com/webstorm/.  Webstorm requires the JDK to be installed.  If you don't already have Java and the JDK installed, please download it here: http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html.

In addition to WebStorm, you will also need to have the Dart SDK installed.  Please download and install the Dart suite (SDK and Dartium):

**Note:** security_monkey is currently pinned to dart v1.12.1 and does not work with newer versions.  Until we fix that, you'll need to download the dart sdk manually at https://www.dartlang.org/downloads/archive/

After we fix the issue, you will be able to use homebrew:

    $ brew tap dart-lang/dart
    $ brew install dart --with-content-shell --with-dartium

**Pro-Tip:** During the Dart installation, make note of the Dart SDK Path, and the Dartium path, as this will be used later during the WebStorm Dart plugin configuration. 
  
For WebStorm to be useful, it will need to have the Dart plugin installed.  You can verify that it is installed by going to WebStorm preferences > Plugins, and searching for "Dart".  If it is checked off, then you have it installed.  If not, then check the box to install it, and click OK.

At this point, you can import the Security Monkey project into WebStorm.  Please reference the WebStorm documentation for details on importing projects.

The Dart plugin needs to be configured to utilize the Dart SDK. To configure the Dart plugin, open WebStorm preferences > Languages & Frameworks > Dart.  If it is not already checked, check "Enable Dart Support for the project ...", and paste in the paths for the Dart SDK path Dartium.
  
- As an example, for a typical Dart OS X installation (via ``brew``), the Dart path will be at: ``/usr/local/opt/dart/libexec``, and the Dartium path will be: ``/usr/local/opt/dart/Chromium.app``

Toggle-On Security Monkey Development Mode
==========================
Once the Dart plugin is configured, you will need to alter a line of Dart code so that Security Monkey can be loaded in your development environment.  You will need to edit the ``dart/lib/util/constants.dart`` file: 

- Comment out the ``API_HOST`` variable under the ``// Same Box`` section, and uncomment the ``API_HOST`` variable under the ``// LOCAL DEV`` section.

Additionally, CSRF protection will cause issues for local development and needs to be disabled.  

- To disable CSRF protection, modify the ``env-config/config-local.py`` file, and set the ``WTF_CSRF_ENABLED`` flag to ``False``.
- **NOTE: DO __NOT__ DO THIS IN PRODUCTION!**

Add Amazon Accounts
==========================
This will add Amazon owned AWS accounts to security monkey. ::

    python manage.py amazon_accounts

Add a user account
==========================
This will add a user account that can be used later to login to the web ui:

    python manage.py create_user email@youremail.com Admin

The first argument is the email address of the new user.  The second parameter is the role and must be one of [anonymous, View, Comment, Justify, Admin].


Start the Security Monkey API
==========================
This starts the REST API that the Angular application will communicate with. ::

    python manage.py runserver

Launch Dartium from within WebStorm
==========================
From within the Security Monkey project in WebStorm, we will launch the UI (inside the Dartium app).

To do this, within the Project Viewer/Explorer, right-click on the ``dart/web/ui.html`` file, and select "Open in Browser" > Dartium.

This will open the Dartium browser with the Security Monkey web UI.

- **Note:** If you get a ``502: Bad Gateway``, try refreshing the page a few times.
- **Another Note:** If the page appears, and then quickly becomes a 404 -- this is normal. The site is attempting to redirect you to the login page.  However, the path for the login page is going to be: ``http://127.0.0.1:8080/login`` instead of the WebStorm port.  This is only present inside of the development environment -- not in production.

Register a user in Security Monkey
==========================
If you didn't create a user on the command line (as instructed earlier), you can create one with the web ui:

Chromium/Dartium will launch and will try to redirect to the login page.  Per the note above, it should result in a 404. This is due to the browser redirecting you to the WebStorm port, and not the NGINX hosted port.  This is normal in the development environment.  Thus, clear your browser address bar, and navigate to: ``http://127.0.0.1:8080/login`` (Note: do not use ``localhost``, use the localhost IP.)
  
Select the Register link (``http://127.0.0.1:8080/register``) to create an account.
  
Log into Security Monkey
==========================
Logging into Security Monkey is done by accessing the login page: ``http://127.0.0.1:8080/login``.  Please note, that in the development environment, when you log in, you will be redirected to ``http://127.0.0.1/None``.  This only occurs in the development environment.  You will need to navigate to the WebStorm address and port (you can simply use WebStorm to re-open the page in Daritum).  Once you are back in Dartium, you will be greeted with the main Security Monkey interface.

Watch an AWS Account
==========================
After you have registered a user, logged in, and re-opened Dartium from WebStorm, you should be at the main Security Monkey interface. Once here, click on Settings and on the *+* to add a new AWS account to sync.

Manually Run the Account Watchers
==========================
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
Continue reading the `Contributing <contributing.rst>`_ guide for additional instructions.

