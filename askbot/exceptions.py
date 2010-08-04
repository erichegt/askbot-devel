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

