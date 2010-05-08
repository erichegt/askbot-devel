"""
Definition of a Singleton wrapper class for livesettings
with interface similar to django.conf.settings
that is each setting has unique key and is accessible
via dotted lookup.

for example to lookup value of setting BLAH you would do

from forum.conf import settings

settings.BLAH

the value will be taken from livesettings database or cache
note that during compilation phase database is not accessible
for the most part, so actual values are reliably available only 
at run time

livesettings is a module developed for satchmo project
"""
from livesettings import SortedDotDict, config_register

class ConfigSettings(object):
    """A very simple Singleton wrapper for settings
    a limitation is that all settings names using this class
    must be distinct, even though they might belong
    to different settings groups
    """
    __instance = None

    def __init__(self):
        """assigns SortedDotDict to self.__instance if not set"""
        if ConfigSettings.__instance == None:
            ConfigSettings.__instance = SortedDotDict()
        self.__dict__['_ConfigSettings__instance'] = ConfigSettings.__instance

    def __getattr__(self, key):
        """value lookup returns the actual value of setting
        not the object - this way only very minimal modifications
        will be required in code to convert an app
        depending on django.conf.settings to livesettings
        """
        return getattr(self.__instance, key).value

    def __setattr__(self, attr, value):
        """ settings crutch is read-only in the program """
        raise Exception('ConfigSettings cannot be changed programmatically')

    def register(self, value):
        """registers the setting
        value must be a subclass of livesettings.Value
        """
        key = value.key
        if key in self.__instance:
            raise Exception('setting %s is already registered' % key)
        else:
            self.__instance[key] = config_register(value)

#settings instance to be used elsewhere in the project
settings = ConfigSettings()
