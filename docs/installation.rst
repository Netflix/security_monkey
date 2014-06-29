============
Installation
============

10 second setup (if you know Python already)
============================================

Just type::

    pip install security_monkey

30 second setup (for anybody)
=============================

- Make sure you have Python 2.7 (`python --version`)
- Download the last `zip of the source code <https://github.com/netflix/security_monkey/master>`_
- Extract all of it where you wish the site to be stored.
- Go to the extracted files::
    
    python setup.py install

Installing Postgres
===================

Security Monkey uses a Postgres database as it's datastore. You can either run Postgres locally or by leveraging RDS. We won't go over how to setup a Postgres database here, but you should make note of the user, password, hostname and database name of the database you setup as these will be used during Security Monkey configuration. 


