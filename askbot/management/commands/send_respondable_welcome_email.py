"""Management command that sends a respondable
welcome email to all users.
User's responses will be used to validate
the email addresses and extract the email signatures.
"""
from django.core.management.base import NoArgsCommand
from askbot.models import User, send_welcome_email

class Command(NoArgsCommand):
    def handle_noargs(self):
        for user in User.objects.filter(email_isvalid = False):
            send_welcome_email(user)
