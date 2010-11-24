"""functions that directly handle user input
"""
import time

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
