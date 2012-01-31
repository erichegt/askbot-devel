================
Optional modules
================

Askbot supports a number of optional modules, enabling certain features, not available 
in askbot by default.

.. _sphinx-search:

Sphinx search
=============
Askbot supports Sphinx search - and at this point only for MySQL.
Tested with sphinx 0.9.8.
May be a little outdated, please give your feedback if that is the case.

To enable:

* install `sphinx search package <http://sphinxsearch.com/>`_
* if necessary to support Chinese language, instead take `sphinx for Chinese <http://code.google.com/p/sphinx-for-chinese/>`_
* prepare configuration file by running command ``python manage.py get_askbot_sphinx_config > sphinx.conf``
* if necessary, modify the ``.conf`` file (may be needed for language other than English
* place the ``sphinx.conf`` file to an appropriate location, like /etc/sphinx/

Install django-sphinx python module (and follow all instructions)

    pip install django-sphinx

In ``settings.py`` add::

    SPHINX_API_VERSION = 0x113 #according to django sphinx doc
    USE_SPHINX_SEARCH = True
    ASKBOT_SPHINX_SEARCH_INDEX = 'askbot'

.. note::
    Value of SPHINX_API_VERSION may depend on the version of 
    python sphinx api installed with the django-sphinx application,
    please refer to the django-sphinx documentation.

Initialize the sphinx index (may need to log in as root)::

    indexer askbot --config /etc/sphinx/sphinx.conf

Start the sphinx search daemon::

    /usr/local/bin/searchd --config /etc/sphinx/sphinx.conf &

Also, add the line above to the file /etc/rc.d/rc.local or equivalent to start the daemon
when the server reboots.

Set up a periodic re-indexing job (using cron)::

    indexer askbot --rotate --config /etc/sphinx/sphinx.conf

Finally, add lin

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

Wordpress Integration 
=====================

To enable authentication for self hosted wordpress sites(wordpress.com blogs will work with openid login). To enable it follow the following steps:

* Check if you have the package `"python_wordpress_xmlrpc <http://pypi.python.org/pypi/python-wordpress-xmlrpc/1.4>`_ from pypi.
* Go to your wordpress blog admin panel and serch for: Settings->Writing->Remote Publishing then check the box for XML-RPC.
* Go back to your askbot site settings and click on *Login Provider Settings* and then activate the option *Activate to allow login with self-hosted wordpress site*, 
* Input your blog url to the xmlrpc.php file it will look something like this http://yoursite.com/xmlrpc.php
* Upload an icon for display in the login area.

After doing this steps you should be able to login with your self hosted wordpress site user/password combination.


Celery for background jobs
==========================

Askbot supports `celery <http://celeryproject.org/>`_ distributed task queue for some task, to enable it follow the following steps:

* Install the following packages: `celery <http://pypi.python.org/pypi/django-celery>`_, `django-celery <http://pypi.python.org/pypi/django-celery>`_,  `django-kombu <http://pypi.python.org/pypi/django-kombu>`_
* Set **CELERY_ALWAYS_EAGER** setting value to **False**
* Run the celery daemon: for this you can use generic init scripts or supervisor, `celery documentation have more information <http://docs.celeryproject.org/en/latest/cookbook/daemonizing.html>`_

For `supervisor <http://supervisord.org/>`_: add this sample config file named askbot.conf into /etc/supervisor/conf.d/ directory::

    [program:askbot_celery]
    command=celeryd --loglevel=INFO

    environment=PYTHONPATH=/path/to/project
    directory=/path/to/project

    user=nobody
    numprocs=1
    stdout_logfile=/var/log/askbot_celery.log
    stderr_logfile=/var/log/askbot_celery.err
    autostart=true
    autorestart=true
    startsecs=10

Then run **supervisorctl update** and it will be started. For more information about job handling with supervisor please visit `this link <http://supervisord.org/>`_.


Receiving replies for email notifications
===========================================

Askbot supports posting replies by email. For this feature  to work ``Lamson`` and ``django-lamson`` need to be installed on the system. To install all the necessery dependencies execute the following command:
    
    pip install django-lamson

The lamson daemon needs a folder to store it's mail queue files and a folder to store log files, create the folders folder named ``run`` and ``logs`` within your project folder by executing the following commands:

    mkdir run

    mkdir logs

The minimum settings required to enable this feature are defining the port and binding address for the lamson SMTP daemon and the email handlers within askbot. Edit your settings.py file to include the following:

    LAMSON_RECEIVER_CONFIG = {'host': 'your.ip.address', 'port': 25}
    
    LAMSON_HANDLERS = ['askbot.lamson_handlers']
    
    LAMSON_ROUTER_DEFAULTS = {'host': '.+'}

In the list of ``installed_apps`` add the app ``django-lamson``.

The ``LAMSON_RECEIVER_CONFIG`` parameter defines the binding address/port for the SMTP daemon. To recieve internet email you will need to bind to your external ip address and port 25. If you just want to test the feature by sending eamil from the same system you could bind to 127.0.0.1 and any higher port. 

To run the lamson SMTP daemon you will need to execute the following management command:
    
    python manage.py lamson_start

To stop the daemon issue the following command

    python manage.py lamson_stop

Note that in order to be able to bind the daemon to port 25 you will need to execute the command as a superuser.

Within the askbot admin interface there are 4 significant configuration points for this feature.

* In the email section, the "Enable posting answers and comments by email" controls whether the feature is enabled or disabled.
* The "reply by email hostname" needs to be set to the email hostname where you want to receive the email replies. If for example this is set to "example.com" the users will post replies to addresses such as "4wffsw345wsf@example.com", you need to point the MX DNS record for that domain to the address where you will run the lamson SMTP daemon.
* The last setting in this section controls the threshold for minimum length of the reply that is posted as an answer to a question. If the user is replying to a notification for a question and the reply  body is shorter than this threshold the reply will be posted as a comment to the question.
* In the karma thresholds section the "Post answers and comments by email" defines the minimum karma for users to be able to post replies by email.

If the system where lamson is hosted also acts as an email server or you simply want some of the emails to be ignored and sent to another server you can define forward rules. Any emails matching these rules will be sent to another smtp server, bypassing the reply by email function. As an example by adding the following in your settings.py file:

    LAMSON_FORWARD = (
        {
           'pattern': '(.*?)@(.subdomain1|subdomain2)\.example.com',
           'host': 'localhost',
           'port': 8825
        },
        {
           'pattern': '(info|support)@example.com',
           'host': 'localhost',
           'port': 8825
        },

    )

any email that was sent to anyaddress@sobdomain1.example.com or anyaddress@sobdomain2.example.com or info@example.com will be forwarded to the smtp server listening on port 8825. The pattern parameter is treated as a regular expression that is matched against  the ``To`` header of the email message and the ``host`` and ``port`` are the host and port of the smtp server that the message should be forwarded to.

If you want to run the lamson daemon on a port other than 25 you can use a mail proxy server such as ``nginx`` that will listen on port 25 and forward any SMTP requests to lamson. Using nginx you can also setup more complex email handling rules, such as for example if the same server where askbot is installed acts as an email server for other domains you can configure nginx to forward any emails directed to your askbot installation to lamson and any other emails to the mail server you're using, such as ``postfix``. For more information on how to use nginx for this please consult the nginx mail module documentation `nginx mail module documentation <http://wiki.nginx.org/MailCoreModule>`_ .
