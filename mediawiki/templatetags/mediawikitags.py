from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
import logging

register = template.Library()

#template tags
class MWPluginFormActionNode(template.Node):
    def __init__(self, wiki_page, form_action):
        self.form_action = ''.join(form_action[1:-1])
        self.wiki_page = ''.join(wiki_page[1:-1])
    def render(self, context):
        out = ('<input type="hidden" name="title" value="%s"/>' \
            + '<input type="hidden" name="command" value="%s"/>') \
            % (self.wiki_page, self.form_action)
        return out

def curry_up_to_two_argument_tag(TagNodeClass):
    def do_the_action_func(parser,token):
        args = token.split_contents()
        if len(args) > 3:
            tagname = token.contents.split()[0]
            raise template.TemplateSyntaxError, \
                    '%s tag requires two arguments or less' % tagname
        if len(args) > 1:
            argument1 = ''.join(args[1][1:-1])
        else:
            argument1 = None
        if len(args) == 3:
            argument2 = ''.join(args[2][1:-1])
        else:
            argument2 = None
        return TagNodeClass(argument1, argument2)
    return do_the_action_func

def do_mw_plugin_form_action(parser,token):
    args = token.split_contents()
    if len(args) != 3:
        tagname = token.contents.split()[0]
        raise template.TemplateSyntaxError, \
                '%s tag requires two arguments' % tagname
    return MWPluginFormActionNode(args[1],args[2])

class MediaWikiPluginUrlNode(template.Node):
    """will return either wiki url, a particular page url
    or a page with command argument to be interpreted by the plugin
    """
    def __init__(self,wiki_page=None,url=None):
        self.url = url
        self.wiki_page = wiki_page
    def render(self,context):
        title_token = '?title=%s' % self.wiki_page
        cmd_token = '&command=%s' % self.url
        if self.wiki_page == None:
            return settings.MEDIAWIKI_URL
        if self.url == None:
            return settings.MEDIAWIKI_URL + title_token
        return settings.MEDIAWIKI_URL + title_token + cmd_token

register.tag('mw_plugin_form_action',do_mw_plugin_form_action)
register.tag('mw_plugin_url',curry_up_to_two_argument_tag(MediaWikiPluginUrlNode))
