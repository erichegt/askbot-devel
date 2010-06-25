.. _pre-requisites:

=========================
Prerequisites for Askbot
=========================
Askbot installation currently requires:

* Python_ version 2.4 - 2.6 (Version 3 is not yet supported)
* MySQL_ version 5
* access to an instance of MySQL database with full privileges

For the production :ref:`deployment` you will also need a webserver capable to run
python web applications.

Creating a database instance
-----------------------------
This section assumes that MySQL is installed and is up and running.

Database can be prepared via your hosting control panel, if available, or
can be created manually as shown below (using a high privilege MySQL account):

Log in to mysql::

    mysql -u username -p

Then type these two commands (note that fake `dbname`, `dbuser`, and `dbpassword` are used in this example)::

    create database askbot DEFAULT CHARACTER SET UTF8 COLLATE utf8_general_ci;
    grant all privileges on dbname.* to dbuser@localhost identified by 'dbpassword';

Again, please remember to create real usernname, database name and password and write them down. These
credentials will go into the file `settings.py`_ - the main configuration file of the Django application.

.. note::

    Notation `dbuser@hostname` is important for security - normally you want to restrict access to
    the database to certain hosts only. `localhost` entry ensures that database cannot be accessed
    from remote hosts at all.

.. _Python: http://www.python.org/download/
.. _MySQL: http://www.mysql.com/downloads/mysql/#downloads 
.. _settings.py: http://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/settings.py
