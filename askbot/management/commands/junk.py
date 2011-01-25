import os
import sys
import tempfile
import threading
from django.core.management.base import NoArgsCommand
from django.core import management

class SEImporterThread(threading.Thread):
    def __init__(self, stdout = None):
        self.stdout = stdout
        super(SEImporterThread, self).__init__()

    def run(self):
        management.call_command('load_stackexchange','/home/fadeev/personal/asksci/asksci.zip')

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        fake_stdout = tempfile.NamedTemporaryFile()
        real_stdout = sys.stdout
        sys.stdout = fake_stdout
        importer = SEImporterThread(stdout = fake_stdout)
        importer.start()

        read_stdout = open(fake_stdout.name, 'r')
        file_pos = 0
        fd = read_stdout.fileno()
        while importer.isAlive():
            c_size = os.fstat(fd).st_size
            if c_size > file_pos:
                line = read_stdout.readline()
                real_stdout.write('Have line :' + line)
                file_pos = read_stdout.tell()

        fake_stdout.close()
        read_stdout.close()
        sys.stdout = real_stdout
