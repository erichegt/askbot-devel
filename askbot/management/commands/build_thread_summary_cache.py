from django.core.management.base import NoArgsCommand
from askbot.models import Thread
from askbot.utils.console import ProgressBar

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        message = "Rebuilding thread summary cache"
        count = Thread.objects.count()
        for thread in ProgressBar(Thread.objects.iterator(), count, message):
            thread.update_summary_html()
