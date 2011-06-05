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

There are two caveats. If you want the "allow posting before logging in" feature
(which can be enabled/disabled at 
"settings"->"data entry and display"->"allow posting before logging in"),
you must either insure that your app calls ``user.post_anonymous_askbot_content()``
right after the user logs in, or activate middleware
``askbot.middleware.anon_posts.PublishAnonPostsMiddleware``.

The middleware solution is not desirable, as it will cause additional 
database queries each time a logged in user loads any page on the site.

Second thing to keep in mind is in askbot each user has records for 
email subscription settings, and these will be missing when user
registers via some alternative login application. This is not a big problem 
and should not lead to errors, however some users may miss email notifications
until their records complete.

The email subscription settings complete automatically when certain pages 
are visited, but there is a way to accelerate this process by calling
management command::

    python manage.py add_missing_subscriptions

Alternatively, you can insert the following call just after the new user
account is created ``user.add_missing_askbot_subscriptions()``
