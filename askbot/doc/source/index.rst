Askbot is a Question and Answer (Q&A) forum whose design is inspired by StackOverflow_ 
and YahooAnswers_ and other similar projects (to lesser extent). 

Askbot is written in Python_ on top of Django_ platform.
Code of Askbot grew out of CNPROG_ project originally written by 
`Mike Chen <http://cn.linkedin.com/in/mikegangchen>`_ and Sailing Cai.

If you have any questions installing or tweaking askbot - please do not hesitate to ask
at the forum_ or email to admin@askbot.org.

Prerequisites
======================
To install and run Askbot the following are required:

* Python_ version 2.4 - 2.6 (Version 3 is not supported)
* MySQL_ version 5

For the production deployment you will also need a webserver capable to run
python web applications (see section Deployment_).

Installation Instructions
===========================

To simplify future deployment, please make sure to use the same python 
interpreter for the installation and testing as the one assigned 
(or will be assigned) to the webserver.

If you already have `easy_install`_ on your system, then type::
 easy_install askbot

If you are using the easy\_install tool, make sure that it was also 
originally installed with the python interpreter mentioned above, 
otherwise use the second method:

Download the latest version of askbot_, unzip and untar the archive and run::
 python setup.py install

If you are planning to use askbot on Windows, please install 
`mysql-python windows binary package <http://www.codegood.com/archives/4>`_ manually.

Chances are that steps above will complete your installation. If so, then 
proceed to the Configuration_ section. Below are extra installation notes
that cover some special cases.

To install in non-standard locations add parameter --prefix=/path/to/some/dir to both commands.

Askbot depends on about a dozen other packages. Normally those dependencies will be
automatically resolved. However, if something does not go well - e.g.
some dependency package site is not accessible, please 
download and install some of those things 
( 
django-1.1.2_, 
django-debug-toolbar_,
South_,
recaptcha-client_,
markdown2_,
html5lib_,
python-openid_,
django-keyedcache_,
django-threaded-multihost_,
mysql-python_
) manually. 

If any of the provided links
do not work please try to look up those packages or notify askbot maintainers at admin@askbot.org.

.. _Configuration:
Configuration
====================

type::
 startforum

and answer questions.

The startforum script will attempt to create necessary directories
and copy files.

If you are creating a new Django project, you will need to edit file

In the case you are adding askbot to an existing Django project, you will need to
merge askbot files settings.py_ and urls.py_ into your project files manually.

Within settings.py, at the very minimum you will need to provide correct values to::
 DATABASE_NAME = ''
 DATABASE_USER = ''
 DATABASE_PASSWORD = '' 

within single quotes - login credential to your mysql database. Assuming that
the database exists, you can now install the tables by running::
 python manage.py syncdb
 python manage.py migrate forum

now run the development sever::
 python manage.py runserver `hostname -i`:8000 #or use some other port number > 1024

`hostname -i` is a Unix command returning the IP address of your system, you can also type 
the IP manually or replace it with localhost if you are installing askbot 
on a local machine.

Your basic installation is now complete. Many settings can be 
changed at runtime by following url /settings.

If you choose to host a real website, please read
section Deployment_. For advice on hosting Askbot, please take 
a look at section Hosting_.

.. _Deployment:
Deployment
==============
Webserver process must be able to write to the following locations::
 /path/to/django-project/log/
 /path/to/django-project/askbot/upfiles

If you know user name or the group name under which the webserver runs,
you can make those directories writable by setting the permissons
accordingly:

For example, if you are using Linux installation of apache webserver running under
group name 'apache' you could do the following::

 chown -R yourlogin:apache /path/to/askbot-site
 chmod -R g+w /path/to/askbot-site/forum/upfiles
 chmod -R g+w /path/to/askbot-site/log

If your account somehow limits you from running such commands - please consult your
system administrator.

Installation under Apache/mod\_wsgi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apache/mod\_wsgi combination is the only type of deployment described in this
document at the moment. mod_wsgi_ is currently the most resource efficient
apache handler for the Python web applications.

The main wsgi script is in the file django.wsgi_
it does not need to be modified

Configure webserver
^^^^^^^^^^^^^^^^^^^^^^

Settings below are not perfect but may be a good starting point::

    WSGISocketPrefix /path/to/socket/sock #must be readable and writable by apache
    WSGIPythonHome /usr/local #must be readable by apache
    WSGIPythonEggs /var/python/eggs #must be readable and writable by apache

    #NOTE: all urs below will need to be adjusted if
    #settings.FORUM_SCRIPT_ALIAS !='' (e.g. = 'forum/')
    #this allows "rooting" forum at http://example.com/forum, if you like
    <VirtualHost ...your ip...:80>
        ServerAdmin forum@example.com
        DocumentRoot /path/to/askbot-site
        ServerName example.com

        #run mod_wsgi process for django in daemon mode
        #this allows avoiding confused timezone settings when
        #another application runs in the same virtual host
        WSGIDaemonProcess askbot
        WSGIProcessGroup askbot

        #force all content to be served as static files
        #otherwise django will be crunching images through itself wasting time
        Alias /m/ /path/to/askbot-site/forum/skins/
        Alias /upfiles/ /path/to/askbot-site/forum/upfiles/
        <Directory /path/to/askbot-site/forum/skins>
            Order deny,allow
            Allow from all
        </Directory>

        #this is your wsgi script described in the prev section
        WSGIScriptAlias / /path/to/askbot-site/django.wsgi

        #this will force admin interface to work only
        #through https (optional)
        #"nimda" is the secret spelling of "admin" ;)
        <Location "/nimda">
            RewriteEngine on
            RewriteRule /nimda(.*)$ https://example.com/nimda$1 [L,R=301]
        </Location>
        CustomLog /var/log/httpd/askbot/access_log common
        ErrorLog /var/log/httpd/askbot/error_log
    </VirtualHost>
    #(optional) run admin interface under https
    <VirtualHost ..your ip..:443>
        ServerAdmin forum@example.com
        DocumentRoot /path/to/askbot-site
        ServerName example.com
        SSLEngine on
        SSLCertificateFile /path/to/ssl-certificate/server.crt
        SSLCertificateKeyFile /path/to/ssl-certificate/server.key
        WSGIScriptAlias / /path/to/askbot-site/django.wsgi
        CustomLog /var/log/httpd/askbot/access_log common
        ErrorLog /var/log/httpd/askbot/error_log
        DirectoryIndex index.html
    </VirtualHost>

Database configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Database can be prepared via your hosting control panel, if available or
can be created manually (provided that you have a mysql account with
a sufficient privilege)

The relevant MySQL the commands are::
 create database askbot DEFAULT CHARACTER SET UTF8 COLLATE utf8_general_ci;
 grant all privileges on dbname.* to dbuser@localhost identified by 'dbpassword';

where dbname, dbuser and dbpassword should be replaced with the real values.
MySQL will create a user with those credentials if it does not yet exist.

Automation of maintenance jobs
===============================

There are routine tasks that should be performed periodically
from the command line. They can be automated via cron_ jobs

File askbot_cron_job_ has a sample script that can be run say hourly

The script currently does two things: (1) sends delayed email alerts and
(2) awards badges. These two actions can be separated into two separate jobs,
if necessary

Sitemap registration
=======================
Sitemap to your forum will be available at url /<settings.FORUM\_SCRIPT\_ALIAS>sitemap.xml
e.g yoursite.com/forum/sitemap.xml or yoursite.com/sitemap.xml

Google will be pinged each time question, answer or
comment is saved or a question deleted.

If you register you sitemap through `Google Webmasters Tools`_ Google 
will have be indexing your site more efficiently.

.. _`Google Webmasters Tools`: https://www.google.com/webmasters/tools/
.. _Python: http://www.python.org/download/
.. _MySQL: http://www.mysql.com/downloads/mysql/#downloads 
.. _YahooAnswers: http://answers.yahoo.com/
.. _StackOverflow: http://stackoverflow.com/
.. _CNPROG: http://cnprog.com
.. _askbot: http://pypi.python.org/pypi/askbot
.. _django-1.1.2: http://www.djangoproject.com/download/1.1.2/tarball/
.. _django-debug-toolbar: http://github.com/robhudson/django-debug-toolbar
.. _South: http://www.aeracode.org/releases/south/
.. _recaptcha-client: http://code.google.com/p/django-recaptcha/
.. _markdown2: http://code.google.com/p/python-markdown2/
.. _html5lib: http://code.google.com/p/html5lib/
.. _python-openid: http://github.com/openid/python-openid
.. _django-keyedcache: http://bitbucket.org/bkroeze/django-keyedcache/src
.. _django-threaded-multihost: http://bitbucket.org/bkroeze/django-threaded-multihost/src
.. _mysql-python-win:
.. _mysql-python: http://sourceforge.net/projects/mysql-python/
.. _settings.py: http://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/settings.py
.. _urls.py: http://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/urls.py
.. _cron: http://www.unixgeeks.org/security/newbie/unix/cron-1.html
.. _mod_wsgi: http://code.google.com/p/modwsgi/
.. _django.wsgi: http://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/django.wsgi
.. _forum: http://askbot.org
.. _askbot_cron_job: http://github.com/ASKBOT/askbot-devel/blob/master/askbot/cron/askbot_cron_job
