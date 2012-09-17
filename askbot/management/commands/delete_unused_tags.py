from django.core.management.base import NoArgsCommand
from django.db import transaction
from askbot import models
from askbot.utils.console import ProgressBar
from askbot.conf import settings as askbot_settings
import sys

class Command(NoArgsCommand):
    @transaction.commit_manually
    def handle_noargs(self, **options):
        tags = models.Tag.objects.all()
        message = 'Searching for unused tags:'
        total = tags.count()
        tags = tags.iterator()
        deleted_tags = list()
        for tag in ProgressBar(tags, total, message):
            if not tag.threads.exists():
                deleted_tags.append(tag.name)
                tag.delete()
            transaction.commit()

        if deleted_tags:
            found_count = len(deleted_tags)
            if found_count == 1:
                print "Found an unused tag %s" % deleted_tags[0]
            else:
                sys.stdout.write("Found %d unused tags" % found_count)
                if found_count > 50:
                    print ", first 50 are:",
                    print ', '.join(deleted_tags[:50]) + '.'
                else:
                    print ": " + ', '.join(deleted_tags) + '.'
            print "Deleted."
        else:
            print "Did not find any."
