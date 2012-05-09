from django.core.management.base import NoArgsCommand
from askbot.conf import settings

class Command(NoArgsCommand):
    '''Loads livesettings values to cache helping speed up
       initial load time for the users'''

    def handle_noargs(self, **options):
        empty1 = emtpy2 = None
        print 'loading cache'
        #Just loads all the settings that way they will be in the cache
        for key, value in settings._ConfigSettings__instance.items():
            empty1 = key
            empty2 = value
        print 'cache pre-loaded'


