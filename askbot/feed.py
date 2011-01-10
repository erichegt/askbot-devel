"""
#-------------------------------------------------------------------------------
# Name:        Syndication feed class for subscription
# Purpose:
#
# Author:      Mike
#
# Created:     29/01/2009
# Copyright:   (c) CNPROG.COM 2009
# Licence:     GPL V2
#-------------------------------------------------------------------------------
"""
#!/usr/bin/env python
#encoding:utf-8
from django.contrib.syndication.feeds import Feed
from django.utils.translation import ugettext as _
from askbot.models import Question
from askbot.conf import settings as askbot_settings
class RssLastestQuestionsFeed(Feed):
    """rss feed class for the latest questions
    """
    title = askbot_settings.APP_TITLE + _(' - ')+ _('latest questions')
    link = askbot_settings.APP_URL
    description = askbot_settings.APP_DESCRIPTION
    #ttl = 10
    copyright = askbot_settings.APP_COPYRIGHT

    def item_link(self, item):
        """get full url to the item
        """
        return self.link + item.get_absolute_url()

    def item_author_name(self, item):
        """get name of author
        """
        return item.author.username

    def item_author_link(self, item):
        """get url of the author's profile
        """
        return item.author.get_profile_url()

    def item_pubdate(self, item):
        """get date of creation for the item
        """
        return item.added_at

    def items(self, item):
        """get questions for the feed
        """
        return Question.objects.filter(
                                    deleted=False
                                ).order_by(
                                    '-last_activity_at'
                                )[:30]

def main():
    """main function for use as a script
    """
    pass

if __name__ == '__main__':
    main()
