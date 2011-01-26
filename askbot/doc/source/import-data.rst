.. import-data::

===============================
Import other forums into Askbot
===============================

At this time only StackExchange import is supported.

There are two ways to import your StackExchange dump into Askbot:

* via the web at url `/import-data/`, relative to your forum installation
* using a management command::

    python manage.py load_stackexchange /path/to/your-se-data.zip

Before importing the data, an entry `askbot.importers.stackexchange` must be added to 
the `INSTALLED_APPS` list in your `settings.py` file and a command `python manage.py syncdb` run
to initialize the stackexchange tables.

In the case your database is not empty at the beginning of the process - **please do back it up**.
