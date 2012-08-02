==========================================================
Setting up Askbot for use on the closed network (Intranet)
==========================================================

When using Askbot on the Intranet (for example - within your 
Company network), it will be useful to disable references to
all external resources - such as custom fonts, gravatars.

Please change the following settings in your ``settings.py`` file::

    ASKBOT_USE_LOCAL_FONTS=True

In addition, in the "live settings":
* disable gravatar in "settings->User settings"
