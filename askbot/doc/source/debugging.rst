This document describes techniques that can be used to debug Askbot and other Django projects
If you discover new debugging techniques, please add here.

===================
USE LOGGING IN CODE
===================

Please remember that log files may contain plaintext passwords, etc.

Please do not add print statements - at least do not commit them to git
because in some environments printing to stdout causes errors

Instead use python logging this way::
    #somewere on top of file
    import logging

    #anywhere below
    logging.debug('this maybe works')
    logging.error('have big error!')
    #or even
    logging.debug('') #this will add time, line number, function and file record 
    #sometimes useful record for call tracing on its own
    #etc - take a look at http://docs.python.org/library/logging.html

in Askbot logging is currently set up in settings.py
please update it if you need - in older revs logging strings have less info

messages of interest can be grepped out of the log file by module/file/function name
e.g. to take out all django_authopenid logs run::
    >grep 'askbot\/django_authopenid' log/django.askbot.log | sed 's/^.*MSG: //'

in the example above `sed` call truncates out a long prefix
and makes output look more meaningful

=====================
DJANGO DEBUG TOOLBAR
=====================

askbot works with django debug toolbar
if debugging under apache server, check 
that debug toolbar media is loaded correctly
if toolbar is enabled but you do not see it, possibly some Alias statement
in apache config is wrong in your VirtualHost or elsewhere
