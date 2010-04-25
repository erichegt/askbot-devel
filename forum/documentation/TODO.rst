note: there is also WISH_LIST. Here is only stuff that will be done soon.

Site looks
===========
* make links within posts blue so that they are visible

Code Cleanups
==============
* remove usage of EXTERNAL_LEGACY_LOGIN
* clean up forum_modules:
  * keep this directory for dependency modules that can be shared
    by multiple apps, 
  * but move other things that are not shared
    inside forum app directory
  * one-by one convert "auto-discovery" modules into 
    regular explicit python imports
* python2.4 incompatibilities
  *  datatime.datetime.strptime

Bugs
======
* make sure that search feature covers questions and answers 
  (title, body, tags)

Refactoring
=============
* merge search, question and index view functions into one

Skins
=======
* organize templates and document them so that
  skins could be more easily created by others
  who are savvy enough
* identify and maybe create snippet-type templates
  and put them into a separate directory 
  for example:
  * gravatar (currently a string in 
    forum/templatetags/extra_tags.py - try inclusion template
    and see if it slows things down a lot)
  * question body
  * answer body
  * datetime widget???
* there is a separator line between posts
  but it shows either before the post or after
  it is nice that separator is lightweight -
  based on css alone - but we need to fix it so that
  it shows only between the posts as a joining item

Features
===========
* new login system, please see 
  http://groups.google.com/group/askbot/browse_thread/thread/1916dfcf666dd56c
  on a separate branch multi-auth-app, then merge
* forum admin interface, some badge configuration

Development environment
==========================
* set up environment for closure development

Project website
====================
* Logo!!! Ideas?
* Adopt Jekyll for project site and transition from Dango
