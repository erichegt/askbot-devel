"""deletes expired sessions from the session database table
works only when sessions are stored in the database
"""
from django.core.management.base import NoArgsCommand
from django.contrib.sessions.models import Session
from optparse import make_option
from askbot.utils.console import ProgressBar
from datetime import datetime

class Command(NoArgsCommand):
    """Django management command class"""

    option_list = NoArgsCommand.option_list + (
            make_option('--quiet',
                action='store_true',
                dest='quiet',
                default=False,
                help="Do not print anything when called."
                ),
            )

    def handle_noargs(self, **options):
        """deletes old sessions"""
        quiet = options.get('quiet', False)

        expired_sessions = Session.objects.filter(
                                expire_date__lt=datetime.now()
                            )
        count = expired_sessions.count()
        expired_sessions = expired_sessions.iterator()
        if quiet is False:
            message = 'There are %d expired sessions' % count
            expired_sessions = ProgressBar(expired_sessions, count, message)

        for session in expired_sessions:
            session.delete()

