.. _compile-time-configuration:

===============================
Initial Configuration of Askbot
===============================

While most configuration settings for askbot can be done at any time :ref:`through the web-interface <run-time-configuration>`, some manipulations on the server are still necessary.

When you are installing askbot the first time you will need to initialize the site setup files by typing::

    startforum

and answering the questions.

The startforum script will attempt to create necessary directories and copy files.

If you are creating a brand new Django project, then you will need to edit file `settings.py`_

In the case you are adding askbot to an existing Django project, you will need to
merge askbot files settings.py_ and urls.py_ into your project files manually.

.. note::

    Files settings.py_ and urls.py_ may also need to be touched up 
    when you upgrate the software, because new versions may bring 
    new dependencies and add new site urls.


Within settings.py, at the very minimum you will need to provide correct values to::

    DATABASE_NAME = ''
    DATABASE_USER = ''
    DATABASE_PASSWORD = '' 

within single quotes - login credentials to your mysql database. 

.. _urls.py: http://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/urls.py
.. _settings.py: http://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/settings.py
