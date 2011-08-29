from django.core.management.base import NoArgsCommand
from askbot.models import User

class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        users = User.objects.all()
        has_avatar = User.objects.filter(has_valid_gravatar= True).count()
        print '%s users in total, %s have valid avatar' % (users.count(), has_avatar) 
        for user in users:
            user.update_has_valid_gravatar()

        print 'Updated all the users'
        has_avatar = User.objects.filter(has_valid_gravatar= True).count()
        print '%s users in total, %s have valid avatar' % (users.count(), has_avatar) 
