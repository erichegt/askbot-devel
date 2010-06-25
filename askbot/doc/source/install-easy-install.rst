.. _install-easy-install:

===========================================================
Installing Askbot with easy_install (python package index).
===========================================================

The latest stable version of askbot can be installed from the official `Python Package Index (PyPI) <http://pypi.python.org/pypi/askbot/>`_

.. note::

    To simplify future deployment, please make sure to use the same python 
    interpreter for the installation and testing as the one assigned 
    (or will be assigned) to the webserver.
    The same applies to easy_install tool, and the `PYTHONPATH`
    environment variable.

If you already have `easy_install`_ (python setuptools) on your system, then type::

 easy_install askbot

If you do not yet have it, download the `askbot archive from PyPI <http://pypi.python.org/pypi/askbot/>`_, unzip and untar it, then run::

 python setup.py install

Both command achieve the same effect, except the second one will also install the setuptools.

.. note::

    To install in non-standard locations add parameter ``--prefix=/path/to/some/dir`` to both commands.

Under windows, please install 
`mysql-python windows binary package <http://www.codegood.com/archives/4>`_ manually.

Most likely, by this time you will have askbot software installed. However, in some cases
one of the dependency packages might fail to install. :ref:`This document <dependencies>` will help you find those components.

When you have all packages installed, 
please proceed to the :ref:`initial configuration <compile-time-configuration>` section. 

.. _Python: http://www.python.org/download/
.. _askbot: http://pypi.python.org/pypi/askbot
.. _`easy_install`: http://pypi.python.org/pypi/setuptools
.. _pypi: http://pypi.python.org/

.. _django.wsgi: http://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/django.wsgi
