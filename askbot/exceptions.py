from django.core import exceptions

class InsufficientReputation(exceptions.PermissionDenied):
    """exception class to indicate that permission
    was denied due to insufficient reputation
    """
    pass

class DuplicateCommand(exceptions.PermissionDenied):
    """exception class to indicate that something
    that can happen only once was attempted for the second time
    """
    pass

class EmailNotSent(exceptions.ImproperlyConfigured):
    """raised when email cannot be sent
    due to some mis-configurations on the server
    """
    pass

