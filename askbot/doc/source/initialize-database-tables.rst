.. _initialize-database-tables:

=======================================================
Initialization and upgrade of the database for Askbot
=======================================================

When you install Askbot the first time and any time you upgrade the software, run these two commands::

    python manage.py syncdb

When you will be suggested to create a superuser, answer **no**.

Then run::

    python manage.py migrate askbot
    python manage.py migrate django_authopenid #embedded login application

.. note::

    When upgrading - do not skip to back up the database before proceeding!!!
    Things can break and it is better to be safe than sorry. Even better -
    do run two installations of your project - one for production deployment
    and the second one - for testing the upgrade. When you are sure that
    your upgrade works, just switch the testing installation for the former production one.

Now run the Django development server and check that everything works::

    python manage.py runserver `hostname -i`:8000 #or use some other port number > 1024

.. note::

    `hostname -i` is a Unix command returning the IP address of your system, you can also type 
    the IP manually or replace it with word `localhost` if you are installing askbot 
    on a local machine.

Finally, register at the site and turn yourself into a superuser by running::

    python manage.py add_admin 1

Here number 1 is the numeric id of the first user, enter a different number, if it is indeed different.

Your basic installation is now complete. Many settings can be 
:ref:`changed at runtime <run-time-configuration>` by following url `/settings`.

If you choose to host a real website, please read
section :ref:`deployment`.


