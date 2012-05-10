from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    '''Loads livesettings values to cache helping speed up
       initial load time for the users'''

    def handle_noargs(self, **options):
        from askbot.conf import settings
        #Just loads all the settings that way they will be in the cache
        for key, value in settings._ConfigSettings__instance.items():
            empty1 = getattr(settings, key)
        print 'cache pre-loaded'
