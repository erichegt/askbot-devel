from django.core.management.base import NoArgsCommand
from askbot.models import Post

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        objs = Post.objects.all()
        print objs
