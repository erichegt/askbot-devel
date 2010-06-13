Intro
=========
ROADMAP aims to streamline activities of the Askbot open source project and
to minimize ad-hoc approaches of "big-picture" level.

Aksbot is a Question and Asnwer system for the normal people!

Let's discuss stuff that goes into this file on
http://groups.google.com/group/askbot

Bacic principles of the project
==================================
Here they are:

* our rule #1 is that all developers have commit right to the project
  repository, but they must follow this ROADMAP and TODO - 
  to keep up with our own sanity.
* we welcome contributions by other people and show tolerance
  and patience - especially to the new team members.
* when users who might not be tech-savvy ask questions -
  we try to answer to the point and using their language 
  (i.e. not programmer jargon:)
* we favor plain and minimalistic style of programming, but pay
  attention to detail - especially details of user experience.

We try do develop using the following workflow:

* specify problem that we try to solve
* create requirements that will guarantee a solution, once met
* dream up some implementation ideas (maybe even some sketches on the paper)
* discuss and decide on the best one
* write and test code

The process doesn't have to be this formal all the time, but trying to stick
to some subset of this almost always helps! 
Especially it helps to iron out disagreements between
individual programmers (which if you are one - you know are qute common
- and they don't all end well :).

Ad-hoc programming - i.e. simply go and add code - is not really encouraged.
This works fine in the one person team or when the team consists of 
best friends, but is almost sure to fail in a heterogenous group.

Architecture and Requirements
=====================================
Obviously Django and Python are pre-made choices - so this
is not going to change any time soon. At this point all of
the client side Javascript is written using jQuery library.

Our basic principle is that Askbot should be a mashable Q&A component.
Askbot is an application written in Python/Django. So it should be 
distributable as a Django App alone or as a whole site (by option).

If we develop sub-systems that can be used in the broader scope - 
we package that thing as a separate django application (login system is one example).

We will start using Google Closure library soon!

Sub-systems
-----------------
* authentication system
* Q&A system
* admin interface
* full text search
* skins (directory forum/skins)

Authentication system
-------------------------
Authentication system will be a separate django application

Here is the discussion thread:
* http://groups.google.com/group/askbot/browse_thread/thread/1916dfcf666dd56c

Most of the requirements are listed in the first message

Skins
-----------
Skins eventually must be upgrade-stable - that is people who created custom
skins should not need to change anything if something changes in the code

Admin interface
-----------------------
* extend forum/settings.py to list default settings of various groups
* create Registry database table the will store setting values
* leave only essential settings that go to the main django settings.py
Create key-value storage
* should some settings be accessible to admins and some to staff???
  for example-secret keys probably should not be shared with staff members
