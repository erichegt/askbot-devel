"""functions that directly handle user input
"""
import sys
import time
from askbot.utils import path

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
        response = raw_input('\n%s (type %s): ' % (prompt_phrase, '/'.join(choices)))
        if response in choices:
            return response
        elif invalid_phrase != None:
            opt_string = ','.join(choices)
            print invalid_phrase % {'opt_string': opt_string}
        time.sleep(1)

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

def print_progress(format_string, progress):
    """print dynamic output of progress of some
    operation to the console and clear the output with
    a backspace character to have the number increment
    in-place"""
    output = format_string % progress
    sys.stdout.write(output)
    sys.stdout.flush()
    sys.stdout.write('\b' * len(output))
    
