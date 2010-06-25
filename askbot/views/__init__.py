"""
.. _askbot.views:

:mod:`askbot.views` - Django views for askbot
=============================================

This module provides `django view functions`_ necessary for the askbot project.

Askbot views are subdivided into the following sub-modules:

* :ref:`readers <askbot.views.readers>` - views that display but do not modify main textual content (Questions, Answers, Comments and Tag)
* :ref:`writers <askbot.views.writers>` - generate forms that change main content 
* :ref:`commands <askbot.views.commands>` - most Ajax command processors
* :ref:`users <askbot.views.users>` - views generating user-specific content and the listing of site users
* :ref:`meta <askbot.views.meta>` - remaining views (for example - badges, faq, privacy, etc. - may require some cleanup)

"""
from askbot.views import readers
from askbot.views import writers
from askbot.views import commands
from askbot.views import users
from askbot.views import meta
