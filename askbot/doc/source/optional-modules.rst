================
Optional modules
================

Askbot supports a number of optional modules, enabling certain features, not available 
in askbot by default.

.. _embedding-video:

Embedding video
===============

Want to share videos in askbot posts? It is possible, but you will have to install a forked 
version of ``markdown2`` module, here is how::

    pip uninstall markdown2
    pip install -e git+git://github.com/andryuha/python-markdown2.git#egg=markdown2

Also, for this to work you'll need to have :ref:`pip` and :ref:`git` installed on your system.

Finally, please go to your forum :ref:`live settings <live-settings>` --> 
"Settings for askbot data entry and display" and check "Enable embedding video".

Limitation: at the moment only YouTube and Veoh are supported.

.. _ldap:

LDAP authentication
===================

To enable authentication via LDAP
(Lightweight Directory Access Protocol, see more info elsewhere)
, first :ref:`install <installation-of-python-packages>`
``python-ldap`` package:

    pip install python-ldap

After that, add configuration parameters in :ref:`live settings <live-settings>`, section
"Keys to connect the site with external services ..." 
(url ``/settings/EXTERNAL_KEYS``, relative to the domain name)

.. note::
    Location of these parameters is likely to change in the future.
    When that happens, an update notice will appear in the documentation.

The parameters are:

* "Use LDAP authentication for the password login" - enable/disable the feature.
  When enabled, the user name and password will be routed to use the LDAP protocol.
  Default system password authentication will be overridden.
* "LDAP service provider name" - any string - just come up with a name for the provider service.
* "URL fro the LDAP service" - a correct url to access the service.
* "Explain how to change the LDAP password"
  - askbot does not provide a method to change LDAP passwords
  , therefore - use this field to explain users how they can change their passwords.

Uploaded avatars
================

To enable uploadable avatars (in addition to :ref:`gravatars <gravatar>`), 
please install development version of
application ``django-avatar``, with the following command:

    pip install -e git+git://github.com/ericflo/django-avatar.git#egg=django-avatar

Then add ``avatar`` to the list of ``INSTALLED_APPS`` in your ``settings.py`` file 
and run (to install database table used by the avatar app):

    python manage.py syncdb

.. note::

    Version of the ``avatar`` application available at pypi may not
    be up to date, so please take the development version from the 
    github repository
