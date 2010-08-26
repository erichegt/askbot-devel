"""
:synopsis: the Django Q&A forum application

Functions in the askbot module perform various
basic actions on behalf of the forum application
"""
import os
import smtplib
from django.core import mail
from django.conf import settings as django_settings
from askbot import exceptions

def get_install_directory():
    """returns path to directory
    where code of the askbot django application 
    is installed
    """
    return os.path.dirname(__file__)

def get_version():
    """returns version of the askbot app
    this version is meaningful for pypi only
    """
    return '0.6.10'

def send_mail(
            subject_line = None,
            body_text = None,
            recipient_list = None,
            activity_type = None,
            related_object = None,
            headers = None,
            raise_on_failure = False,
        ):
    """sends email message
    logs email sending activity
    and any errors are reported as critical
    in the main log file

    related_object is not mandatory, other arguments
    are. related_object (if given, will be saved in
    the activity record)

    if raise_on_failure is True, exceptions.EmailNotSent is raised
    """
    #print subject_line
    #print body_text
    try:
        msg = mail.EmailMessage(
                        subject_line, 
                        body_text, 
                        django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list,
                        headers = headers
                    )
        msg.content_subtype = 'html'
        msg.send()
        if related_object is not None:
            assert(activity_type is not None)
    except Exception, e:
        logging.critical(unicode(e))
        if raise_on_failure == True:
            raise exceptions.EmailNotSent(unicode(e))
