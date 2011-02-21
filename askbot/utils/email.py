from django.core.mail import EmailMultiAlternatives
from django.conf import settings as django_settings
from django.template import loader, Context
from django.utils.html import strip_tags
from threading import Thread

def send_email(
            subject,
            recipients,
            template,
            context = {},
            sender = django_settings.DEFAULT_FROM_EMAIL,
            txt_template = None
        ):
    context['settings'] = django_settings
    html_body = loader.get_template(template).render(Context(context))

    if txt_template is None:
        txt_body = strip_tags(html_body)
    else:
        txt_body = loader.get_template(txt_template).render(Context(context))

    msg = EmailMultiAlternatives(subject, txt_body, sender, recipients)
    msg.attach_alternative(html_body, "text/html")

    thread = Thread(target=EmailMultiAlternatives.send,  args=[msg])
    thread.setDaemon(True)
    thread.start()
