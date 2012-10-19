"""this management commands will fix corrupted posts
that do not have revisions by creating a fake initial revision
based on the content stored in the post itself
"""
from django.core.management.base import NoArgsCommand
from askbot import models
from askbot import const
from askbot.utils.console import ProgressBar

def print_results(items):
    template = 'id=%d, title=%s'
    for thread in items:
        print template % (thread.id, thread.title.encode('utf8'))

class Command(NoArgsCommand):
    """Command class for "fix_bodyless_questions"
    """
    def handle(self, *arguments, **options):
        """function that handles the command job
        """
        threads = models.Thread.objects.all()
        count = threads.count()
        message = 'Looking for body-less questions'
        bodyless = list()
        multi_body = list()
        for thread in ProgressBar(threads.iterator(), count, message):
            body_count = models.Post.objects.filter(
                                    thread=thread,
                                    post_type='question',
                                ).count()
            if body_count == 0:
                bodyless.append(thread)
            elif body_count > 1:
                multi_body.append(thread)

        if len(bodyless) + len(multi_body) == 0:
            print 'None found.'
        else:
            if len(bodyless):
                print '\nQuestions without body text:'
                print_results(bodyless)
            if len(multi_body):
                print '\nQuestions with >1 instances of body text'
                print_results(multi_body)
