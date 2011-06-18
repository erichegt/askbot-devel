from django.core.management.base import NoArgsCommand
from django.db.models import Count
from django.db import transaction
from askbot.models import User
from askbot import forms

class Command(NoArgsCommand):
    @transaction.commit_manually
    def handle_noargs(self, **options):
        for user in User.objects.all():
            user.add_missing_askbot_subscriptions()
            transaction.commit()
