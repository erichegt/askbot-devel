from django.http import HttpResponse

# Merge with original namespace so user
# doesn't have to import twice.
from django.shortcuts import *


__all__ = ('render_to_string', 'render_to_response',)


# Is within ``template.loader`` as per Django specification -
# but I think it fits very well here.
from coffin.template.loader import render_to_string


def render_to_response(template_name, dictionary=None, context_instance=None,
                       mimetype=None):
    """
    :param template_name: Filename of the template to get or a sequence of
        filenames to try, in order.
    :param dictionary: Rendering context for the template.
    :returns: A response object with the evaluated template as a payload.
    """
    rendered = render_to_string(template_name, dictionary, context_instance)
    return HttpResponse(rendered, mimetype=mimetype)
