"""functions that send email in askbot
these automatically catch email-related exceptions
"""
import os
import smtplib
import logging
from django.core import mail
from django.conf import settings as django_settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from askbot import exceptions
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot.utils import url_utils
from askbot.utils.file_utils import store_file
#todo: maybe send_mail functions belong to models
#or the future API
def prefix_the_subject_line(subject):
    """prefixes the subject line with the
    EMAIL_SUBJECT_LINE_PREFIX either from
    from live settings, which take default from django
    """
    prefix = askbot_settings.EMAIL_SUBJECT_PREFIX
    if prefix != '':
        subject = prefix.strip() + ' ' + subject.strip()
    return subject

def extract_first_email_address(text):
    """extract first matching email address
    from text string
    returns ``None`` if there are no matches
    """
    match = const.EMAIL_REGEX.search(text)
    if match:
        return match.group(0)
    else:
        return None

def thread_headers(post, orig_post, update):
    """modify headers for email messages, so
    that emails appear as threaded conversations in gmail"""
    suffix_id = django_settings.SERVER_EMAIL
    if update == const.TYPE_ACTIVITY_ASK_QUESTION:
        msg_id = "NQ-%s-%s" % (post.id, suffix_id)
        headers = {'Message-ID': msg_id}
    elif update == const.TYPE_ACTIVITY_ANSWER:
        msg_id = "NA-%s-%s" % (post.id, suffix_id)
        orig_id = "NQ-%s-%s" % (orig_post.id, suffix_id)
        headers = {'Message-ID': msg_id,
                  'In-Reply-To': orig_id}
    elif update == const.TYPE_ACTIVITY_UPDATE_QUESTION:
        msg_id = "UQ-%s-%s-%s" % (post.id, post.last_edited_at, suffix_id)
        orig_id = "NQ-%s-%s" % (orig_post.id, suffix_id)
        headers = {'Message-ID': msg_id,
                  'In-Reply-To': orig_id}
    elif update == const.TYPE_ACTIVITY_COMMENT_QUESTION:
        msg_id = "CQ-%s-%s" % (post.id, suffix_id)
        orig_id = "NQ-%s-%s" % (orig_post.id, suffix_id)
        headers = {'Message-ID': msg_id,
                  'In-Reply-To': orig_id}
    elif update == const.TYPE_ACTIVITY_UPDATE_ANSWER:
        msg_id = "UA-%s-%s-%s" % (post.id, post.last_edited_at, suffix_id)
        orig_id = "NQ-%s-%s" % (orig_post.id, suffix_id)
        headers = {'Message-ID': msg_id,
                  'In-Reply-To': orig_id}
    elif update == const.TYPE_ACTIVITY_COMMENT_ANSWER:
        msg_id = "CA-%s-%s" % (post.id, suffix_id)
        orig_id = "NQ-%s-%s" % (orig_post.id, suffix_id)
        headers = {'Message-ID': msg_id,
                  'In-Reply-To': orig_id}
    else:
        # Unknown type -> Can't set headers
        return {}

    return headers

def send_mail(
            subject_line = None,
            body_text = None,
            from_email = django_settings.DEFAULT_FROM_EMAIL,
            recipient_list = None,
            activity_type = None,
            related_object = None,
            headers = None,
            raise_on_failure = False,
        ):
    """
    todo: remove parameters not relevant to the function
    sends email message
    logs email sending activity
    and any errors are reported as critical
    in the main log file

    related_object is not mandatory, other arguments
    are. related_object (if given, will be saved in
    the activity record)

    if raise_on_failure is True, exceptions.EmailNotSent is raised
    """
    try:
        assert(subject_line is not None)
        subject_line = prefix_the_subject_line(subject_line)
        msg = mail.EmailMessage(
                        subject_line, 
                        body_text, 
                        from_email,
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
                ).filter(
                    is_active = True
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

ASK_BY_EMAIL_USAGE = _(
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
        error_message = string_concat(error_message, ASK_BY_EMAIL_USAGE)
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
    send_mail(
        recipient_list = (email,),
        subject_line = 'Re: ' + subject,
        body_text = error_message
    )

def process_attachments(attachments):
    """saves file attachments and adds
    
    cheap way of dealing with the attachments
    just insert them inline, however it might
    be useful to keep track of the uploaded files separately
    and deal with them as with resources of their own value"""
    if attachments:
        content = ''
        for att in attachments:
            file_storage, file_name, file_url = store_file(att)
            chunk = '[%s](%s) ' % (att.name, file_url)
            file_extension = os.path.splitext(att.name)[1]
            #todo: this is a hack - use content type
            if file_extension.lower() in ('.png', '.jpg', '.gif'):
                chunk = '\n\n!' + chunk
            content += '\n\n' + chunk
        return content
    else:
        return ''



def process_emailed_question(from_address, subject, body, attachments = None):
    """posts question received by email or bounces the message"""
    #a bunch of imports here, to avoid potential circular import issues
    from askbot.forms import AskByEmailForm
    from askbot.models import User
    data = {
        'sender': from_address,
        'subject': subject,
        'body_text': body
    }
    form = AskByEmailForm(data)
    if form.is_valid():
        email_address = form.cleaned_data['email']
        try:
            user = User.objects.get(
                        email__iexact = email_address
                    )
        except User.DoesNotExist:
            bounce_email(email_address, subject, reason = 'unknown_user')
        except User.MultipleObjectsReturned:
            bounce_email(email_address, subject, reason = 'problem_posting')

        tagnames = form.cleaned_data['tagnames']
        title = form.cleaned_data['title']
        body_text = form.cleaned_data['body_text']

        try:
            body_text += process_attachments(attachments)
            user.post_question(
                title = title,
                tags = tagnames,
                body_text = body_text
            )
        except PermissionDenied, error:
            bounce_email(
                email_address,
                subject,
                reason = 'permission_denied',
                body_text = unicode(error)
            )
    else:
        #error_list = list()
        #for field_errors in form.errors.values():
        #    error_list.extend(field_errors)

        if from_address:
            bounce_email(
                from_address,
                subject,
                reason = 'problem_posting',
                #body_text = '\n*'.join(error_list)
            )
