"""functions that send email in askbot
these automatically catch email-related exceptions
"""
import smtplib
import logging
from django.core import mail
from django.conf import settings as django_settings
from askbot.conf import settings as askbot_settings
from askbot import exceptions
#todo: maybe send_mail functions belong to models
#or the future API
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
    prefix = askbot_settings.EMAIL_SUBJECT_PREFIX.strip() + ' '
    try:
        assert(subject_line is not None)
        subject_line = prefix + subject_line
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
    except Exception, error:
        logging.critical(unicode(error))
        if raise_on_failure == True:
            raise exceptions.EmailNotSent(unicode(error))

def mail_moderators(
            subject_line = '',
            body_text = '',
            raise_on_failure = False):
    """sends email to forum moderators and admins
    """
    from django.db.models import Q
    from askbot.models import User
    recipient_list = User.objects.filter(
                    Q(status='m') | Q(is_superuser=True)
                ).values_list('email', flat=True)
    recipient_list = set(recipient_list)

    from_email = ''
    if hasattr(django_settings, 'DEFAULT_FROM_EMAIL'):
        from_email = django_settings.DEFAULT_FROM_EMAIL

    try:
        mail.send_mail(subject_line, body_text, from_email, recipient_list)
    except smtplib.SMTPException, error:
        logging.critical(unicode(error))
        if raise_on_failure == True:
            raise exceptions.EmailNotSent(unicode(error))
