"""Copyright 2011 Askbot.org and Askbot project contributors.

Custom management command that takes questions posted
via email at the IMAP server
Expects subject line of emails to have format:
[Tag1, Tag2] Question title

Tags can be entered as multiword, but the space character
within the tag may be replaced with a dash, per live 
setting EMAIL_REPLACE_SPACE_IN_TAGS
also, to make use of this command, the feature must
be enabled via ALLOW_ASKING_BY_EMAIL
and IMAP settings in the settings.py must be configured
correctly

todo: use templates for the email formatting
"""
import imaplib
import email
import quopri
import base64
from django.conf import settings as django_settings
from django.core.management.base import NoArgsCommand, CommandError
from django.core import exceptions
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.core.urlresolvers import reverse
from askbot.conf import settings as askbot_settings
from askbot.utils import mail
from askbot.utils import url_utils
from askbot import models
from askbot.forms import AskByEmailForm

USAGE = _(
"""<p>To ask by email, please:</p>
<ul>
    <li>Format the subject line as: [Tag1; Tag2] Question title</li>
    <li>Type details of your question into the email body</li>
</ul>
<p>Note that tags may consist of more than one word, and tags
may be separated by a semicolon or a comma</p>
"""
)

def bounce_email(email, subject, reason = None, body_text = None):
    """sends a bounce email at address ``email``, with the subject
    line ``subject``, accepts several reasons for the bounce:

    * ``'problem_posting'``, ``unknown_user`` and ``permission_denied``
    * ``body_text`` in an optional parameter that allows to append
      extra text to the message
    """
    if reason == 'problem_posting':
        error_message = _(
            '<p>Sorry, there was an error posting your question '
            'please contact the %(site)s administrator</p>'
        ) % {'site': askbot_settings.APP_SHORT_NAME}
        error_message = string_concat(error_message, USAGE)
    elif reason == 'unknown_user':
        error_message = _(
            '<p>Sorry, in order to post questions on %(site)s '
            'by email, please <a href="%(url)s">register first</a></p>'
        ) % {
            'site': askbot_settings.APP_SHORT_NAME,
            'url': url_utils.get_login_url()
        }
    elif reason == 'permission_denied':
        error_message = _(
            '<p>Sorry, your question could not be posted '
            'due to insufficient privileges of your user account</p>'
        )
    else:
        raise ValueError('unknown reason to bounce an email: "%s"' % reason)

    if body_text != None:
        error_message = string_concat(error_message, body_text)

    #print 'sending email'
    #print email
    #print subject
    #print error_message
    mail.send_mail(
        recipient_list = (email,),
        subject_line = 'Re: ' + subject,
        body_text = error_message
    )

class CannotParseEmail(Exception):
    """This exception will bounce the email"""
    def __init__(self, email, subject):
        super(CannotParseEmail, self).__init__()
        bounce_email(email, subject, reason = 'problem_posting')

def parse_message(msg):
    """returns a tuple
    (<from email address>, <subject>, <body>)
    the function will attempt to decode the email
    supported encodings are "quoted-printable" and "base64"
    not supported - emails using language - specific encodings
    """
    sender = msg.get('From')
    subject = msg.get('Subject')
    if msg.is_multipart():
        msg = msg.get_payload()
        if isinstance(msg, list):
            raise CannotParseEmail(sender, subject)

    ctype = msg.get_content_type()#text/plain only
    raw_body = msg.get_payload()#text/plain only
    encoding = msg.get('Content-Transfer-Encoding')
    if encoding == 'base64':
        body = base64.b64decode(raw_body)
    elif encoding == 'quoted-printable':
        body = quopri.decodestring(raw_body)
    else:
        body = raw_body
    return (sender, subject, body)


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        """reads all emails from the INBOX of
        imap server and posts questions based on
        those emails. Badly formatted questions are
        bounced, as well as emails from unknown users

        all messages are deleted thereafter
        """
        if not askbot_settings.ALLOW_ASKING_BY_EMAIL:
            raise CommandError('Asking by email is not enabled')

        #open imap server and select the inbox
        if django_settings.IMAP_USE_TLS:
            imap_getter = imaplib.IMAP4_SSL
        else:
            imap_getter = imaplib.IMAP4
        imap = imap_getter(
            django_settings.IMAP_HOST,
            django_settings.IMAP_PORT
        )
        imap.login(
            django_settings.IMAP_HOST_USER,
            django_settings.IMAP_HOST_PASSWORD
        )
        imap.select('INBOX')

        #get message ids
        status, ids = imap.search(None, 'ALL')

        if len(ids[0].strip()) == 0:
            #with empty inbox - close and exit
            imap.close()
            imap.logout()
            return

        #for each id - read a message, parse it and post a question
        for id in ids[0].split(' '):
            t, data = imap.fetch(id, '(RFC822)')
            message_body = data[0][1]
            msg = email.message_from_string(data[0][1])
            imap.store(id, '+FLAGS', '\\Deleted')
            try:
                (sender, subject, body) = parse_message(msg)
            except CannotParseEmail, e:
                continue
            data = {
                'sender': sender,
                'subject': subject,
                'body_text': body
            }
            form = AskByEmailForm(data)
            print data
            if form.is_valid():
                email_address = form.cleaned_data['email']
                try:
                    user = models.User.objects.get(
                                email__iexact = email_address
                            )
                except models.User.DoesNotExist:
                    bounce_email(email_address, subject, reason = 'unknown_user')
                except models.User.MultipleObjectsReturned:
                    bounce_email(email_address, subject, reason = 'problem_posting')

                tagnames = form.cleaned_data['tagnames']
                title = form.cleaned_data['title']
                body_text = form.cleaned_data['body_text']

                try:
                    user.post_question(
                        title = title,
                        tags = tagnames,
                        body_text = body_text
                    )
                except exceptions.PermissionDenied, e:
                    bounce_email(
                        email_address,
                        subject,
                        reason = 'permission_denied',
                        body_text = unicode(e)
                    )
            else:
                email_address = mail.extract_first_email_address(sender)
                if email_address:
                    bounce_email(
                        email_address,
                        subject,
                        reason = 'problem_posting'
                    )
        imap.expunge()
        imap.close()
        imap.logout()
