from django import http
from django.template import Context, RequestContext
from coffin.template.loader import render_to_string


__all__ = ('page_not_found', 'server_error', 'shortcut')


# no Jinja version for this needed
from django.views.defaults import shortcut


def page_not_found(request, template_name='404.html'):
    """
    Default 404 handler.

    Templates: `404.html`
    Context:
        request_path
            The path of the requested URL (e.g., '/app/pages/bad_page/')
    """
    content = render_to_string(template_name,
        RequestContext(request, {'request_path': request.path}))
    return http.HttpResponseNotFound(content)


def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: `500.html`
    Context: None
    """
    content = render_to_string(template_name, Context({}))
    return http.HttpResponseServerError(content)
