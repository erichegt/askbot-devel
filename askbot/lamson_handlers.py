import re
from lamson.routing import route, stateless
from lamson.server import Relay
from django.utils.translation import ugettext as _
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from askbot.models import ReplyAddress
from askbot.utils import mail


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

def process_attachment(part):
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

def get_body(message):
    """returns plain text body of the message"""
    body = message.body()
    if body:
        return body
    for part in message.walk():
        if is_body(part):
            return part.body

def get_attachments(message):
    """returns a list of file attachments
    represented by StringIO objects"""
    attachments = list()
    for part in message.walk():
        if is_attachment(part):
            attachments.append(process_attachment(part))
    return attachments

@route('ask@(host)')
@stateless
def ASK(message, host = None):
    body = get_body(message)
    attachments = get_attachments(message)
    from_address = message.From
    subject = message['Subject']#why lamson does not give it normally?
    mail.process_emailed_question(from_address, subject, body, attachments)


@route('reply-(address)@(host)', address='.+')
@stateless
def PROCESS(message, address = None, host = None):
    """handler to process the emailed message
    and make a post to askbot based on the contents of
    the email, including the text body and the file attachments"""
    try:
        for rule in settings.LAMSON_FORWARD:
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
        separator = _("======= Reply above this line. ====-=-=")
        parts = get_body(message).split(separator)
        attachments = get_attachments(message)
        if len(parts) != 2 :
            error = _("Your message was malformed. Please make sure to qoute \
                the original notification you received at the end of your reply.")
        else:
            reply_part = parts[0]
            reply_part = '\n'.join(reply_part.splitlines(True)[:-3])
            #the function below actually posts to the forum
            if reply_address.was_used:
                reply_address.edit_post(
                    reply_part.strip(),
                    attachments = attachments
                )
            else:
                reply_address.create_reply(
                    reply_part.strip(),
                    attachments = attachments
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
        from askbot.utils import mail
        from django.template import Context
        from askbot.skins.loaders import get_template

        template = get_template('reply_by_email_error.html')
        body_text = template.render(Context({'error':error}))
        mail.send_mail(
            subject_line = "Error posting your reply",
            body_text = body_text,
            recipient_list = [message.From],
        )        
