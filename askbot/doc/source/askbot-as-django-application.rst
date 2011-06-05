=====================================
Askbot as reusable django application
=====================================

Askbot can be used both as as dedicated site and as an application
within a larger site. There are still issues to resolve to make askbot
a truly reusable app, but some are already solved.

This page is a guide for using askbot as an independent app and it is 
somewhat technical.

Using alternative login system
==============================

Askbot has a bundled application for user login and registration,
but it can be replaced with any other.
Just remove ``'askbot.deps.django_authopenid'``
from the ``INSTALLED_APPS``,
remove ``'askbot.deps.django_authopenid.backends.AuthBackend'``
from the ``AUTHENTICATION_BACKENDS``,
install another registration app
and modify ``LOGIN_URL`` accordingly.

There are three caveats.

Firstly, if you are using some other login/registration app,
please disable feature
"settings"->"data entry and display"->"allow posting before logging in".

This may be fixed in the future by adding a snippet of code to run
right after the user logs in - please ask at askbot forum if you are 
interested.

Secondly, disable setting "settings"->"user settings"->"allow add and remove login methods".
This one is specific to the builtin login application.

One more thing to keep in mind is in askbot each user has records for 
email subscription settings, and these will be missing when he/she
registers via some alternative login application.
This is not a big problem and should not lead to errors,
however some users may miss email notifications
until their records complete.

The email subscription settings are created automatically when certain pages 
are visited, but there is a way to accelerate this process by calling
management command::

    python manage.py add_missing_subscriptions

Alternatively, you can insert the following call just after the new user
account is created ``user.add_missing_askbot_subscriptions()``
