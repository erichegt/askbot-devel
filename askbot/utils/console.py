"""functions that directly handle user input
"""
import sys
import time
import logging
from askbot.utils import path

def start_printing_db_queries():
    """starts logging database queries into console,
    should be used for debugging only"""
    logger = logging.getLogger('django.db.backends')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

def choice_dialog(prompt_phrase, choices = None, invalid_phrase = None):
    """prints a prompt, accepts keyboard input
    and makes sure that user response is one of given
    in the choices argument, which is required
    and must be a list

    invalid_phrase must be a string with %(opt_string)s
    placeholder
    """
    assert(hasattr(choices, '__iter__'))
    assert(not isinstance(choices, basestring))
    while 1:
        response = raw_input(
            '\n%s (type %s)\n> ' % (prompt_phrase, '/'.join(choices))
        )
        if response in choices:
            return response
        elif invalid_phrase != None:
            opt_string = ','.join(choices)
            print invalid_phrase % {'opt_string': opt_string}
        time.sleep(1)


def simple_dialog(prompt_phrase, required=False):
    """asks user to enter a string, if `required` is True,
    will repeat question until non-empty input is given
    """
    while 1:

        if required:
            prompt_phrase += ' (required)'

        response = raw_input(prompt_phrase + '\n> ').strip()
        
        if response or required is False:
            return response

        time.sleep(1)


def get_yes_or_no(prompt_phrase):
    while True:
        response = raw_input(prompt_phrase + ' (yes/no)\n> ').strip()
        if response in ('yes', 'no'):
            return response
            

def open_new_file(prompt_phrase, extension = '', hint = None):
    """will ask for a file name to be typed
    by user into the console path to the file can be
    either relative or absolute. Extension will be appended
    to the given file name.
    Return value is the file object.
    """
    if extension != '':
        if extension[0] != '.':
            extension = '.' + extension
    else:
        extension = ''

    file_object = None
    if hint:
        file_path = path.extend_file_name(hint, extension)
        file_object = path.create_file_if_does_not_exist(file_path, print_warning = True)
        
    while file_object == None:
        file_path = raw_input(prompt_phrase)
        file_path = path.extend_file_name(file_path, extension)
        file_object = path.create_file_if_does_not_exist(file_path, print_warning = True)

    return file_object

def print_action(action_text, nowipe = False):
    """print the string to the standard output
    then wipe it out to clear space
    """
    #for some reason sys.stdout.write does not work here
    #when action text is unicode
    print action_text,
    sys.stdout.flush()
    if nowipe == False:
        #return to the beginning of the word
        sys.stdout.write('\b' * len(action_text))
        #white out the printed text
        sys.stdout.write(' ' * len(action_text))
        #return again
        sys.stdout.write('\b' * len(action_text))
    else:
        sys.stdout.write('\n')

def print_progress(elapsed, total, nowipe = False):
    """print dynamic output of progress of some
    operation, in percent, to the console and clear the output with
    a backspace character to have the number increment
    in-place"""
    output = '%6.2f%%' % (100 * float(elapsed)/float(total))
    print_action(output, nowipe)

class ProgressBar(object):
    """A wrapper for an iterator, that prints 
    a progress bar along the way of iteration
    """
    def __init__(self, iterable, length, message = ''):
        self.iterable = iterable
        self.length = length
        self.counter = float(0)
        self.max_barlen = 60
        self.curr_barlen = 0
        self.progress = ''
        if message and length > 0:
            print message
 

    def __iter__(self):
        return self

    def print_progress_bar(self):
        """prints the progress bar"""

        self.backspace_progress_percent()

        tics_to_write = 0
        if self.length < self.max_barlen:
            tics_to_write = self.max_barlen/self.length
        elif int(self.counter) % (self.length/self.max_barlen) == 0:
            tics_to_write = 1

        if self.curr_barlen + tics_to_write <= self.max_barlen:
            sys.stdout.write('-' * tics_to_write)
            self.curr_barlen += tics_to_write

        self.print_progress_percent()

    def backspace_progress_percent(self):
        sys.stdout.write('\b'*len(self.progress))

    def print_progress_percent(self):
        """prints percent of achieved progress"""
        self.progress = ' %.2f%%' % (100 * (self.counter/self.length))
        sys.stdout.write(self.progress)
        sys.stdout.flush()

    def finish_progress_bar(self):
        """brint the last bars, to make all bars equal length"""
        self.backspace_progress_percent()
        sys.stdout.write('-' * (self.max_barlen - self.curr_barlen))

    def next(self):

        try:
            result = self.iterable.next()
        except StopIteration:
            if self.length > 0:
                self.finish_progress_bar()
                self.print_progress_percent()
                sys.stdout.write('\n')
            raise

        self.print_progress_bar()
        self.counter += 1
        return result
