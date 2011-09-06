from django.core.management.base import NoArgsCommand
from django.contrib.sessions.models import Session
from django.db import transaction
from askbot.utils.console import print_progress
from datetime import datetime

DELETE_LIMIT = 100 

class Command(NoArgsCommand):

    @transaction.commit_manually
    def handle_noargs(self, **options):
        '''deletes old sessions'''
        verbosity = options.get('verbosity', '0')
        expired_session_count  = Session.objects.filter(expire_date__lt=datetime.now()).count()
        transaction.commit()
        if verbosity > '1':
            print "There are %d expired sessions" % expired_session_count

        while 1:
            s = Session.objects.filter(expire_date__lt=datetime.now())[:DELETE_LIMIT]
            count = s.count()
            transaction.commit()
            if count > 0:
                for session in s:
                    session.delete()
                transaction.commit()
                if verbosity > '1':
                    print_progress(count, expired_session_count, True)
            else:
                break

        if verbosity > '1':
            print "sessions cleared"
