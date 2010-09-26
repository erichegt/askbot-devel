from django.contrib.syndication.feeds import *       # merge modules

import sys
from django.contrib.syndication.feeds import Feed as DjangoFeed
from coffin.template import loader as coffin_loader


class Feed(DjangoFeed):
    """A ``Feed`` implementation that renders it's title and
    description templates using Jinja2.

    Unfortunately, Django's base ``Feed`` class is not very extensible
    in this respect at all. For a real solution, we'd have to essentially
    have to duplicate the whole class. So for now, we use this terrible
    non-thread safe hack.

    Another, somewhat crazy option would be:
        * Render the templates ourselves through Jinja2 (possible
          introduce new attributes to avoid having to rewrite the
          existing ones).
        * Make the rendered result available to Django/the superclass by
          using a custom template loader using a prefix, say
          "feed:<myproject.app.views.MyFeed>". The loader would simply
          return the Jinja-rendered template (escaped), the Django template
          mechanism would find no nodes and just pass the output through.
    Possible even worse than this though.
    """

    def get_feed(self, *args, **kwargs):
        parent_module = sys.modules[DjangoFeed.__module__]
        old_loader = parent_module.loader
        parent_module.loader = coffin_loader
        try:
            return super(Feed, self).get_feed(*args, **kwargs)
        finally:
            parent_module.loader = old_loader