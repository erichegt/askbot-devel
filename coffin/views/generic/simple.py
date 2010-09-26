import inspect

from django.views.generic.simple import *
from coffin.template import loader, RequestContext

exec inspect.getsource(direct_to_template)
