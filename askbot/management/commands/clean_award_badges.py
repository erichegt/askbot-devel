"""
#-------------------------------------------------------------------------------
# Name:        Award badges command
# Purpose:     This is a command file croning in background process regularly to
#              query database and award badges for user's special acitivities.
#
# Author:      Mike
#
# Created:     18/01/2009
# Copyright:   (c) Mike 2009
# Licence:     GPL V2
#-------------------------------------------------------------------------------
"""
#!/usr/bin/env python
#encoding:utf-8
from django.core.management.base import NoArgsCommand
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from askbot import models

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        try:
            try:
                self.clean_awards()
            except Exception, e:
                print e
        finally:
            connection.close()

    def clean_awards(self):
        models.Award.objects.all().delete()

        award_type =ContentType.objects.get_for_model(models.Award)
        models.Activity.objects.filter(content_type=award_type).delete()

        for user in models.User.objects.all():
            user.gold = 0
            user.silver = 0
            user.bronze = 0
            user.save()

        for badge in models.Badge.objects.all():
            badge.awarded_count = 0
            badge.save()
            
        query = "UPDATE activity SET is_auditted = 0"
        cursor = connection.cursor()
        try:
            cursor.execute(query)
        finally:
            cursor.close()
            connection.close()

def main():
    pass

if __name__ == '__main__':
    main()
