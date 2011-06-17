.. import-data::

===============================
Import other forums into Askbot
===============================

Askbot supports importing of data from StackExchange and Zendesk.

.. warning::
    If your database contains any data prior to importing, please back it up before proceeding.

StackExchange
=============

Add `askbot.importers.stackexchange` to the list of `INSTALLED_APPS` list in your `settings.py`, then run::
    python manage.py syncdb

Then there will be two ways to import your StackExchange dump:

* via the web at url `/import-data/`, relative to your forum installation
* using a management command::

    python manage.py load_stackexchange /path/to/your-se-data.zip

In the case your database is not empty at the beginning of the process - **please do back it up**.

Zendesk
=======
Add `askbot.importers.zendesk` to the list of `INSTALLED_APPS` in the `settings.py`,
run `python manage.py syncdb`.

Prepare your zendesk files: put all your .xml files into one directory and tar-zip it::

    mkdir somedir
    mv *.xml somedir #select the zendesk xml files and move them to the directory
    tar cvfz zendesk.tgz somedir #name of the tgz file is not important

Then run the import script::

    python manage.py import_zendesk zendesk.tgz #file name is the parameter
