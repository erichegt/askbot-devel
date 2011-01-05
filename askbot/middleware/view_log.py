"""This module records the site visits by the authenticaded
users and heps maintain the state of the search (for all visitors).

Included here is the ViewLogMiddleware and the helper class ViewLog.
"""
import logging
import datetime
from django.conf import settings
from askbot.models import signals
from django.views.static import serve
from askbot.views.readers import questions as questions_view
from askbot.views.commands import vote
from askbot.views.writers import delete_comment, post_comments, retag_question
from askbot.views.readers import revisions

#todo: the list is getting bigger and bigger - maybe there is a better way to
#trigger reset of sarch state?
IGNORED_VIEWS = (serve, vote, delete_comment, post_comments,
                retag_question, revisions)

class ViewLog(object):
    """The ViewLog helper obejcts store the trail of the page visits for a
    given user. The trail is recorded only up to a certain depth.

    The purpose to record this info is to reset the search state
    when the user walks "too far away" from the search page.
    
    These objects must be modified only in this middlware.
    """
    def __init__(self):
        self.views = []
        self.depth = 3 #todo maybe move this to const.py

    def get_previous(self, num):
        """get a previous record from a certain depth"""
        if num > self.depth - 1:
            raise Exception("view log depth exceeded")
        elif num < 0:
            raise Exception("num must be positive")
        elif num <= len(self.views) - 1:
            return self.views[num]
        else:
            return None

    def set_current(self, view_name):
        """insert a new record"""
        self.views.insert(0, view_name)
        if len(self.views) > self.depth:
            self.views.pop()

    def __str__(self):
        return str(self.views) + ' depth=%d' % self.depth

class ViewLogMiddleware(object):
    """ViewLogMiddleware does two things: tracks visits of pages for the
    stateful site search and sends the site_visited signal
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        #send the site_visited signal for the authenticated users
        if request.user.is_authenticated():
            signals.site_visited.send(None, #this signal has no sender
                user = request.user,
                timestamp = datetime.datetime.now()
            )

        #remaining stuff is for the search state
        if view_func == questions_view:
            view_str = 'questions'
        elif view_func in IGNORED_VIEWS:
            return
        else:
            view_str = view_func.__name__
            if view_str == 'wrap':
                return

        if settings.DEBUG == True:
            #todo: dependency!
            try:
                from debug_toolbar.views import debug_media as debug_media_view
                if view_func == debug_media_view:
                    return
            except ImportError:
                pass

        logging.debug('user %s, view %s' % (request.user.username, view_str))
        logging.debug('next url is %s' % request.REQUEST.get('next','nothing'))

        if 'view_log' in request.session:
            view_log = request.session['view_log']
        else:
            view_log = ViewLog()

        view_log.set_current(view_str)
        request.session['view_log'] = view_log
