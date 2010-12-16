from django.core import management
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """Dumps askbot forum data into the file for the later use with "load_forum"

usage: python manage.py dump_forum > somefile.json

.json file extension is mandatory
"""
    def handle(self, *args, **options):
        management.call_command(
                            'dumpdata',
                            exclude = ('contenttypes',),
                            indent = 4
                        )
