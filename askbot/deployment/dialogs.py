"""functions that directly handle user input
"""
from askbot.deployment import messages
import time

def multiple_choice_input(prompt_phrase, options = None):
    """prints a prompt, accepts keyboard input
    and makes sure that user response is one of given
    in the options argument, which is required
    and must be a list
    """
    assert(isinstance(options, list))
    while 1:
        response = raw_input('\n%s (type %s): ' % (prompt_phrase, '/'.join(options)))
        if response in options:
            return response
        else:
            opt_string = ','.join(options)
            print messages.INVALID_INPUT % {'opt_string': opt_string}
            time.sleep(1)
