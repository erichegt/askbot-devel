import threading
from django.core import management
import logging

class ImporterThread(threading.Thread):
    def __init__(self, dump_file = None):
        self.dump_file = dump_file
        super(ImporterThread, self).__init__()

    def run(self):
        management.call_command('load_stackexchange', self.dump_file)
