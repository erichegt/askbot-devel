import sys
import optparse
from django.core import management
from django.core.management.base import BaseCommand
from askbot.utils import console

class Command(BaseCommand):
    help = """Dumps askbot forum data into the file for the later use with "load_forum".
The extension ".json" will be added automatically."""

    option_list = BaseCommand.option_list + (
            optparse.make_option('--dump-name',
                type = 'str',
                dest = 'dump_file'
            ),
        )
    def handle(self, *args, **options):
        dump_file = console.open_new_file(
                        'Please enter file name (no extension): ',
                        hint = options.get('dump_file', None),
                        extension = '.json'
                    )
        print "Saving file %s ..." % dump_file.name
        stdout_orig = sys.stdout
        try:
            sys.stdout = dump_file
            management.call_command(
                                'dumpdata',
                                #exclude = ('contenttypes',),
                                indent = 4
                            )
            sys.stdout = stdout_orig
            print "Done."
        except KeyboardInterrupt:
            sys.stdout = stdout_orig
            print "\nCanceled."
