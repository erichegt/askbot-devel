import sys
from django.core.management.base import NoArgsCommand
from django.db import transaction
from askbot import models
from askbot.utils import console
from askbot.models import signals

FORMAT_STRING = '%6.2f%%'

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        signal_data = signals.pop_all_db_signal_receivers()
        self.run_command()
        signals.set_all_db_signal_receivers(signal_data)

    @transaction.commit_manually
    def run_command(self):
        """method that runs the actual command"""

        questions = models.Question.objects.all()
        checked_count = 0
        found_count = 0
        total_count = questions.count()
        print "Searching for questions with incomplete tag records:",
        for question in questions:

            tags = question.tags.all()
            denorm_tag_set = set(question.get_tag_names())
            norm_tag_set = set(question.tags.values_list('name', flat=True))
            if norm_tag_set != denorm_tag_set:

                if question.last_edited_by:
                    user = question.last_edited_by
                    timestamp = question.last_edited_at
                else:
                    user = question.author
                    timestamp = question.added_at

                question.update_tags(
                    tagnames = question.tagnames,
                    user = user,
                    timestamp = timestamp
                )
                found_count += 1
            transaction.commit()
            checked_count += 1
            progress = 100*float(checked_count)/float(total_count)
            console.print_progress(FORMAT_STRING, progress)
        print FORMAT_STRING % 100
        if found_count:
            print '%d problem questions found, tag records restored' % found_count
        else:
            print 'Nothing found'
