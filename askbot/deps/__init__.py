"""
.. _askbot.deps

:mod:askbot.deps - dependency packages for Askbot
===================================================

Most askbot dependencies are satisfied with setuptools, but some modules
were either too seriously modified - like `django_authopenid` specifically for 
askbot, while others are not available via PyPI. Yet some other packages 
while being listed on PyPI, still do not install reliably - those were also
added to the ``askbot.deps`` module.

Some packages included here were modified with hardcoded imports like::

    from askbot.deps.somepackage import xyz
    from askbot.deps import somepackage

So these cannot be moved around at all.

There is one package - ``python.openid`` which has not been modified this way.
In order for this one to import, PYTHONPATH variable was modified within `django.wsgi`_
file - the connector script for Apache mod_wsgi.

"""
