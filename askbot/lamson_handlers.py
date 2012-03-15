import re
from lamson.routing import route, stateless
from lamson.server import Relay
from django.utils.translation import ugettext as _
from askbot.models import ReplyAddress
from django.conf import settings
from StringIO import StringIO


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

def get_dispositions(part):
    """return list of part's content dispositions
    or an empty list
    """
    disposition_hdr = part.get('Content-Disposition', None)
    if disposition_hdr:
        dispositions = disposition_hdr.strip().split(';')
        return [disp.lower() for disp in dispositions]
    else:
        return list()

def is_attachment(part):
    """True if part content disposition is
    attachment"""
    dispositions = get_dispositions(part)
    if len(dispositions) == 0:
        return False

    if dispositions[0] == 'attachment':
        return True
        
    return False

def process_attachment(part):
    """takes message part and turns it into StringIO object"""
    file_data = part.get_payload(decode = True)
    att = StringIO(file_data)
    att.content_type = part.get_content_type()
    att.size = len(file_data)
    att.name = None#todo figure out file name
    att.create_date = None
    att.mod_date = None
    att.read_date = None

    dispositions = get_dispositions(part)[:1]
    for disp in dispositions:
        name, value = disp.split('=')
        if name == 'filename':
            att.name = value
        elif name == 'create-date':
            att.create_date = value
        elif name == 'modification-date':
            att.modification_date = value
        elif name == 'read-date':
            att.read_date = value

    return att

def get_attachments(message):
    """returns a list of file attachments
    represented by StringIO objects"""
    attachments = list()
    for part in message.walk():
        if is_attachment(part):
            attachments.append(process_attachment(part))
    return attachments



@route("(address)@(host)", address=".+")
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
        reply_address = ReplyAddress.objects.get_unused(address, message.From)
        separator = _("======= Reply above this line. ====-=-=")
        parts = message.body().split(separator)
        attachments = get_attachments(message)
        if len(parts) != 2 :
            error = _("Your message was malformed. Please make sure to qoute \
                the original notification you received at the end of your reply.")
        else:
            reply_part = parts[0]
            reply_part = '\n'.join(reply_part.splitlines(True)[:-3])
            #the function below actually posts to the forum
            reply_address.create_reply(
                reply_part.strip(),
                attachments = attachments
            )
    except ReplyAddress.DoesNotExist:
        error = _("You were replying to an email address\
         unknown to the system or you were replying from a different address from the one where you\
         received the notification.")
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



