from django.core.management.base import NoArgsCommand
from django.db.models import Count
from django.db import transaction
from askbot.models import User
from askbot import forms

class Command(NoArgsCommand):
    @transaction.commit_manually
    def handle_noargs(self, **options):
        users = User.objects.annotate(
                    subscription_count = Count('notification_subscriptions')
                ).filter(subscription_count = 0)
        for user in users:
            form = forms.SimpleEmailSubscribeForm({'subscribe':'y'})
            form.full_clean()
            form.save(user=user)
            transaction.commit()
