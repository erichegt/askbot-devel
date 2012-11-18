"""`group_messages` is a django application
which allows users send messages to other users
and groups (instances of :class:`django.contrib.auth.models.Group`)

The same methods are used are used to send messages
to users as to groups - achieved via special "personal groups".

By convention - personal groups have names formatted as follows:
_personal_<user id>, for example for the user whose `id == 1`,
the group should be named `'_personal_1'`.

Only one person must be a member of a personal group and
each user must have such group.

TODO: decouple this application
first step is to package send_mail separately
"""
