import re
import functools
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings as django_settings
from django.template import Context
from django.utils.translation import ugettext as _
from lamson.routing import route, stateless
from lamson.server import Relay
from askbot.models import ReplyAddress, Tag
from askbot.utils import mail
from askbot.conf import settings as askbot_settings
from askbot.skins.loaders import get_template


#we might end up needing to use something like this
#to distinguish the reply text from the quoted original message
"""
def _strip_message_qoute(message_text):
    import re
    result = message_text
    pattern = "(?P<qoute>" + \
        "On ([a-zA-Z0-9, :/<>@\.\"\[\]]* wrote:.*)|" + \
        "From: [\w@ \.]* \[mailto:[\w\.]*@[\w\.]*\].*|" + \
        "From: [\w@ \.]*(\n|\r\n)+Sent: [\*\w@ \.,:/]*(\n|\r\n)+To:.*(\n|\r\n)+.*|" + \
        "[- ]*Forwarded by [\w@ \.,:/]*.*|" + \
        "From: [\w@ \.<>\-]*(\n|\r\n)To: [\w@ \.<>\-]*(\n|\r\n)Date: [\w@ \.<>\-:,]*\n.*|" + \
        "From: [\w@ \.<>\-]*(\n|\r\n)To: [\w@ \.<>\-]*(\n|\r\n)Sent: [\*\w@ \.,:/]*(\n|\r\n).*|" + \
        "From: [\w@ \.<>\-]*(\n|\r\n)To: [\w@ \.<>\-]*(\n|\r\n)Subject:.*|" + \
        "(-| )*Original Message(-| )*.*)"
    groups = re.search(pattern, email_text, re.IGNORECASE + re.DOTALL)
    qoute = None
    if not groups is None:
        if groups.groupdict().has_key("qoute"):
            qoute = groups.groupdict()["qoute"]
    if qoute:
        result = reslut.split(qoute)[0]
    #if the last line contains an email message remove that one too
    lines = result.splitlines(True)
    if re.search(r'[\w\.]*@[\w\.]*\].*', lines[-1]):
        result = '\n'.join(lines[:-1])
    return result
"""

def get_disposition(part):
    """return list of part's content dispositions
    or an empty list
    """
    dispositions = part.content_encoding.get('Content-Disposition', None)
    if dispositions:
        return dispositions[0]
    else:
        return list()

def get_attachment_info(part):
    return part.content_encoding['Content-Disposition'][1]

def is_attachment(part):
    """True if part content disposition is
    attachment"""
    return get_disposition(part) == 'attachment'

def is_inline_attachment(part):
    """True if part content disposition is
    inline"""
    return get_disposition(part) == 'inline'

def format_attachment(part):
    """takes message part and turns it into SimpleUploadedFile object"""
    att_info = get_attachment_info(part) 
    name = att_info.get('filename', None)
    content_type = get_content_type(part)
    return SimpleUploadedFile(name, part.body, content_type)

def get_content_type(part):
    """return content type of the message part"""
    return part.content_encoding.get('Content-Type', (None,))[0]

def is_body(part):
    """True, if part is plain text and is not attachment"""
    if get_content_type(part) == 'text/plain':
        if not is_attachment(part):
            return True
    return False

def get_part_type(part):
    if is_body(part):
        return 'body'
    elif is_attachment(part):
        return 'attachment'
    elif is_inline_attachment(part):
        return 'inline'

def get_parts(message):
    """returns list of tuples (<part_type>, <formatted_part>),
    where <part-type> is one of 'body', 'attachment', 'inline'
    and <formatted-part> - will be in the directly usable form:
    * if it is 'body' - then it will be unicode text
    * for attachment - it will be django's SimpleUploadedFile instance

    There may be multiple 'body' parts as well as others
    usually the body is split when there are inline attachments present.
    """

    parts = list()

    if message.body():
        parts.append(('body', message.body()))

    for part in message.walk():
        part_type = get_part_type(part)
        if part_type == 'body':
            part_content = part.body
        elif part_type in ('attachment', 'inline'):
            part_content = format_attachment(part)
        else:
            continue
        parts.append((part_type, part_content))
    return parts

def process_reply(func):
    @functools.wraps(func)
    def wrapped(message, host = None, address = None):
        """processes forwarding rules, and run the handler
        in the case of error, send a bounce email
        """
        try:
            for rule in django_settings.LAMSON_FORWARD:
                if re.match(rule['pattern'], message.base['to']):
                    relay = Relay(host=rule['host'], 
                               port=rule['port'], debug=1)
                    relay.deliver(message)
                    return
        except AttributeError:
            pass

        error = None
        try:
            reply_address = ReplyAddress.objects.get(
                                            address = address,
                                            allowed_from_email = message.From
                                        )

            #here is the business part of this function
            func(
                from_address = message.From,
                subject_line = message['Subject'],
                parts = get_parts(message),
                reply_address_object = reply_address
            )

        except ReplyAddress.DoesNotExist:
            error = _("You were replying to an email address\
             unknown to the system or you were replying from a different address from the one where you\
             received the notification.")
        except Exception, e:
            import sys
            sys.stderr.write(str(e))
            import traceback
            sys.stderr.write(traceback.format_exc())

        if error is not None:
            template = get_template('email/reply_by_email_error.html')
            body_text = template.render(Context({'error':error}))
            mail.send_mail(
                subject_line = "Error posting your reply",
                body_text = body_text,
                recipient_list = [message.From],
            )        

    return wrapped

@route('(addr)@(host)', addr = '.+')
@stateless
def ASK(message, host = None, addr = None):
    """lamson handler for asking by email,
    to the forum in general and to a specific group"""

    #we need to exclude some other emails by prefix
    if addr.startswith('reply-'):
        return
    if addr.startswith('welcome-'):
        return

    parts = get_parts(message)
    from_address = message.From
    subject = message['Subject']#why lamson does not give it normally?
    if addr == 'ask':
        mail.process_emailed_question(from_address, subject, parts)
    else:
        if askbot_settings.GROUP_EMAIL_ADDRESSES_ENABLED == False:
            return
        try:
            group_tag = Tag.group_tags.get(
                deleted = False,
                name__iexact = addr
            )
            mail.process_emailed_question(
                from_address, subject, parts, tags = [group_tag.name, ]
            )
        except Tag.DoesNotExist:
            #do nothing because this handler will match all emails
            return
        except Tag.MultipleObjectsReturned:
            return

@route('welcome-(address)@(host)', address='.+')
@stateless
@process_reply
def VALIDATE_EMAIL(
    parts = None,
    reply_address_object = None,
    **kwargs
):
    """process the validation email and save
    the email signature
    todo: go a step further and
    """
    content, stored_files = mail.process_parts(parts)
    reply_code = reply_address_object.address
    if reply_code in content:

        #extract the signature
        tail = list()
        for line in reversed(content.splitlines()):
            #scan backwards from the end until the magic line
            if reply_code in line:
                break
            tail.insert(0, line)

        #strip off the leading quoted lines, there could be one or two
        while tail[0].startswith('>'):
            line.pop(0)

        signature = '\n'.join(tail)

        #save the signature and mark email as valid
        user = reply_address_object.user
        user.email_signature = signature
        user.email_isvalid = True
        user.save()

        data = {
            'site_name': askbot_settings.APP_SHORT_NAME,
            'site_url': askbot_settings.APP_URL,
            'ask_address': 'ask@' + askbot_settings.REPLY_BY_EMAIL_HOSTNAME
        }
        template = get_template('email/re_welcome_lamson_on.html')

        mail.send_mail(
            subject_line = _('Re: Welcome to %(site_name)s') % data,
            body_text = template.render(Context(data)),
            recipient_list = [from_address,]
        )

    else:
        raise ValueError(
            _(
                'Please reply to the welcome email '
                'without editing it'
            )
        )

@route('reply-(address)@(host)', address='.+')
@stateless
@process_reply
def PROCESS(
    parts = None,
    reply_address_object = None,
    **kwargs
):
    """handler to process the emailed message
    and make a post to askbot based on the contents of
    the email, including the text body and the file attachments"""
    if reply_address_object.was_used:
        reply_address_object.edit_post(parts)
    else:
        reply_address_object.create_reply(parts)
