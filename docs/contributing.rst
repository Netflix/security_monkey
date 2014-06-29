************
Contributing
************

Contributions to Security Monkey are welcome! Here are some tips to get you started
hacking on Security Monkey and contributing back your patches.


Development setup
=================

1. Make sure you have the following Python versions installed:

   - CPython 2.7


2. Create and activate a virtualenv::

       virtualenv ve
       source ve/bin/activate

3. Install development dependencies::

       pip install nose mock moto


4. Run tests.

   For a quick test suite run, using the virtualenv's Python version::

       nosetests

5. Start the development server:

       python manage.py runserver

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
