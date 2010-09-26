"""Makes the template filters from the ``django.contrib.markup`` app
available to both the Jinja2 and Django engines.

In other words, adding ``coffin.contrib.markup`` to your INSTALLED_APPS
setting will enable the markup filters not only through Coffin, but
also through the default Django template system.
"""

from coffin.template import Library as CoffinLibrary
from django.contrib.markup.templatetags.markup import register


# Convert Django's Library into a Coffin Library object, which will
# make sure the filters are correctly ported to Jinja2.
register = CoffinLibrary.from_django(register)