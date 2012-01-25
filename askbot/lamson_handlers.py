import re
import logging
from lamson.routing import route, route_like, stateless
from django.utils.translation import ugettext as _
from askbot.models import ReplyAddress
from askbot.conf import settings as askbot_settings




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



@route("(address)@(host)", address=".+")
@stateless
def PROCESS(message, address = None, host = None):

    error = None
    try:
        reply_address = ReplyAddress.objects.get_unused(address, message.From)
        separator = _("======= Reply above this line. ====-=-=")
        parts = message.body().split(separator)
        if len(parts) != 2 :
            error = _("Your message was malformed. Please make sure to qoute \
                the original notification you received at the end of your reply.")
        else:
            reply_part = parts[0]
            reply_part = '\n'.join(reply_part.splitlines(True)[:-3])
            reply_address.create_reply(reply_part.strip())
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


