from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
import sys

class Command(NoArgsCommand):
    def get_user(self, uid_str):
        try:
            uid = int(uid_str)
            return User.objects.get(id=uid)
        except User.DoesNotExist:
            print 'sorry there is no user with id=%d' % uid
            sys.exit(1)
        except ValueError:
            print 'user id must be integer, have %s' % uid_str
            sys.exit(1)

    def parse_arguments(self, arguments):
        if len(arguments) != 1:
            print 'argument for this command id <user_id>'
            sys.exit(1)
        self.user = self.get_user(arguments[0])

    def confirm_action(self):
        u = self.user
        print ''
        prompt = 'Do you really wish to REMOVE user (id=%d, name=%s) from the list of site admins? yes/no: ' \
                % (u.id, u.username)
        str = raw_input(prompt)
        if str != 'yes':
            print 'action canceled'
            sys.exit(1)

    def remove_signals(self):
        pre_save.receivers = []
        post_save.receivers = []

    def handle(self, *arguments, **options):
        #destroy pre_save and post_save signals
        self.parse_arguments(arguments)
        self.confirm_action()
        self.remove_signals()

        self.user.remove_admin_status()
        self.user.save()
