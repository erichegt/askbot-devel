================
Optional modules
================

Askbot supports a number of optional modules, enabling certain features, not available 
in askbot by default.

Follow users
============

Install ``django-followit`` app::

    pip install -e git+git://github.com/ASKBOT/django-followit.git#egg=followit

Then add ``followit`` to the ``INSTALLED_APPS`` and run ``syncdb`` management command.

Uploaded avatars
================

To enable uploadable avatars (in addition to :ref:`gravatars <gravatar>`), 
please install development version of
application ``django-avatar``, with the following command::

    pip install -e git+git://github.com/ericflo/django-avatar.git#egg=django-avatar

Then add ``avatar`` to the list of ``INSTALLED_APPS`` in your ``settings.py`` file 
and run (to install database table used by the avatar app):

    python manage.py syncdb

Also, settings ``MEDIA_ROOT`` and ``MEDIA_URL`` will need to be added to your ``settings.py`` file.

.. note::

    Version of the ``avatar`` application available at pypi may not
    be up to date, so please take the development version from the 
    github repository
