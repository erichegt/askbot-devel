"""patches for the coffin module"""
from jinja2 import nodes
from jinja2 import Markup
from jinja2.ext import Extension

class CsrfTokenExtension(Extension):
    """Jinja2-version of the ``csrf_token`` tag.

    Adapted from a snippet by Jason Green:
    http://www.djangosnippets.org/snippets/1847/

    This tag is a bit stricter than the Django tag in that it doesn't
    simply ignore any invalid arguments passed in.
    """

    tags = set(['csrf_token'])

    def parse(self, parser):
        lineno = parser.stream.next().lineno
        return nodes.Output([
            self.call_method('_render', [nodes.Name('csrf_token', 'load')])
        ]).set_lineno(lineno)

    def _render(self, csrf_token):
        from django.template.defaulttags import CsrfTokenNode
        return Markup(CsrfTokenNode().render({'csrf_token': csrf_token}))

def add_csrf_token_tag():
    """adds csrf token tag to the default library"""
    import coffin.template.defaulttags
    coffin.template.defaulttags.CsrfTokenExtension = CsrfTokenExtension
    csrf_token = CsrfTokenExtension
    coffin.template.defaulttags.csrf_token = csrf_token
    coffin.template.defaulttags.register.tag(csrf_token)
