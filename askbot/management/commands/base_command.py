"""
#-------------------------------------------------------------------------------
# Name:        Award badges command
# Purpose:     This is a command file croning in background process regularly to
#              query database and award badges for user's special acitivities.
#
# Author:      Mike, Sailing
#
# Created:     22/01/2009
# Copyright:   (c) Mike 2009
# Licence:     GPL V2
#-------------------------------------------------------------------------------
"""
#!/usr/bin/env python
#encoding:utf-8

from django.core.management.base import NoArgsCommand

class BaseCommand(NoArgsCommand):
    def update_activities_auditted(self, cursor, activity_ids):
        # update processed rows to auditted
        if len(activity_ids):
            query = "UPDATE activity SET is_auditted = True WHERE id in (%s)"\
                    % ','.join('%s' % item for item in activity_ids)
            cursor.execute(query)
