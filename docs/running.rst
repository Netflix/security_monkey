=======
Running
=======

.. NOTE::
	Before attempting to run Security Monkey ensure they you have followed the steps outline in :doc:`installation <./installation>` and :doc:`configuration <./configuration>`


.. WARNING::
    Running Security Monkey from the command line is not advised for a production installation see :doc:`using nginx <./nginx_install>` and :doc:`using supervisor <./using_supervisor>`


Creating the database
=====================

Before starting Security Monkey you will need to setup the database you created during installation. You should only have to do this step once:

	python manage.py init db

This will use the database defined in your configuration and create the tables needed for security monkey to run

Starting the API
================

- Run with admin rights::

    python manage.py run_api_server


Starting the scheduler
======================

Security Monkey relies on a scheduler task to poll other accounts for policy information. The API will function fine without this process but you will not receive updated policy information.

- Run::

	python manage.py scheduler


Running the Web GUI
====================

.. NOTE::
	To run the Web UI you will need to install and configure Nginx see :doc:`using nginx <./nginx_install>`

When you have Nginx configured you should be able to connect the GUI on the 127.0.0.1 or by the FQDN you have configured in the Security Monkey config file.


Running in background
=====================

Security Monkey doesn't come with something built in for this. You have several solutions.

*For a small website or just to play around:*

Just make it a shell background process. E.G in GNU/Linux::

  nohup python manage.py run_api_server

Or run it in a screen.


