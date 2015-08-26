************
Development Setup on Ubuntu
************

Please follow the instructions below for setting up the Security Monkey development environment on Ubuntu Trusty (14.04).

AWS Credentials
==========================
You will need to have the proper IAM Role configuration in place.  See `Configuration <configuration.rst>`_ for more details.  Additionally, you will need to have IAM keys available within your environment variables.  There are many ways to accomplish this.  Please see Amazon's documentation for additional details: http://docs.aws.amazon.com/general/latest/gr/getting-aws-sec-creds.html.
  
Additionally, see the boto documentation for more information: http://boto.readthedocs.org/en/latest/boto_config_tut.html

Install Primary Packages:
==========================
These must be installed first. ::

    sudo apt-get install git git-flow python-pip postgresql postgresql-contrib libpq-dev python-dev nginx libffi-dev

Setup Virtualenv
==========================
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

Clone Security Monkey
==========================
Clone the security monkey code repository. ::

    cd ~
    git clone https://github.com/Netflix/security_monkey.git
    cd security_monkey

Install Pip Requirements
==========================
Pip will install all the dependencies into the current virtualenv. ::

    pip install -r requirements.txt

SECURITY_MONKEY_SETTINGS
  Set the environment variable in your current session that tells Flask where the conifguration file is located. ::

    export SECURITY_MONKEY_SETTINGS=`pwd`/env-config/config-local.py
    # Note - I like to append this to the virtualenv activate script
    vi $HOME/virtual_envs/security_monkey/bin/activate
    export SECURITY_MONKEY_SETTINGS=$HOME/security_monkey/env-config/config-local.py

Configure PostgreSQL
==========================
Create a PostgreSQL database for security monkey and add a role.  Set the timezone to GMT. ::

    sudo -u postgres psql
    CREATE DATABASE "securitymonkeydb";
    CREATE ROLE "securitymonkeyuser" LOGIN PASSWORD 'securitymonkeypass';
    CREATE SCHEMA securitymonkeydb
    GRANT Usage, Create ON SCHEMA "securitymonkeydb" TO "securitymonkeyuser";
    set timezone TO 'GMT';
    select now();
    \q

Init the Security Monkey DB
==========================
Run Alembic/FlaskMigrate to create all the database tables. ::

    python manage.py db upgrade

Configure NGINX
==========================
On Ubuntu, the NGINX configuration files will be located at: ``/etc/nginx``. You will need to make a modification to the nginx.conf file. The configuration changes include the following:

- Disabling port 8080 for the main nginx.conf file
- Importing the Security Monkey specific configuration

Open the main NGINX configuration file: ``/etc/nginx/nginx.conf``, and in the ``http`` section, add the line ::
  
    include securitymonkey.conf;

Next, in the file: ``/etc/nginx/sites-enabled/default``, comment out the ``listen`` line (under the ``server`` section) ::

    server {
      listen 80 default_server;   # Comment out this line by placing a '#' in front of 'listen'
  
Next, you will create the ``securitymonkey.conf`` NGINX configuration file.  Create this file under ``/etc/nginx/``, and paste in the following (MAKE NOTE OF SPECIFIC SECTIONS) ::
  
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

NGINX can be started by running the ``sudo nginx`` command in the console.  You will need to run ``sudo nginx`` before moving on.  This will also output any errors that are encountered when reading the configuration files.

Launch and Configure the WebStorm Editor:
==========================
We prefer the WebStorm IDE for developing with Dart: https://www.jetbrains.com/webstorm/.  Webstorm requires the JDK to be installed.  If you don't already have Java installed, then install it by running the commands: ::

  sudo apt-get install default-jre default-jdk

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

Toggle-On Security Monkey Development Mode
==========================
Once the Dart plugin is configured, you will need to alter a line of Dart code so that Security Monkey can be loaded in your development environment.  You will need to edit the ``dart/lib/util/constants.dart`` file: 

- Comment out the ``API_HOST`` variable under the ``// Same Box`` section, and uncomment the ``API_HOST`` variable under the ``// LOCAL DEV`` section.

Additionally, CSRF protection will cause issues for local development and needs to be disabled.  

- To disable CSRF protection, modify the ``env-config/config-local.py`` file, and set the ``WTF_CSRF_ENABLED`` flag to ``False``.
- **NOTE: DO __NOT__ DO THIS IN PRODUCTION!**

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
