"""
Middleware that strips whitespace between html tags
copied from David Cramer's blog
http://www.davidcramer.net/code/369/spaceless-html-in-django.html
"""
from django.utils.html import strip_spaces_between_tags as short
 
class SpacelessMiddleware(object):
    def process_response(self, request, response):
        """strips whitespace from all documents
        whose content type is text/html
        """
        if 'text/html' in response['Content-Type']:
            response.content = short(response.content)
        return response
