This document is a map for our activities down the road - therefore ROADMAP.
ROADMAP does not specify deadlines - those belong to the PENDING file

Intro
=========
ROADMAP aims to streamline activities of the OSQA open source project and
to minimize ad-hoc approaches of "big-picture" level.

With one exception: under extreme time pressure improvised approaches are perfectly acceptable.

Items in this document must be discussed in public via dev@osqa.net

Architecture
=============

Sub-systems
-----------------
* authentication system
* Q&A system

Authentication system
-------------------------
* MUST authenticate people visiting the website via web browsers.
* Upon successful authentication must associates the visitor with 
  his/her Django system user account
* MUST allow multiple methods of authentication to the same account
* MUST support a method to recover lost authentication link by email
* MAY offer an option to "soft-validate" user's email (send a link 
  with a special key, so that user clicks and we know that email is valid)
  "soft" - meaning that lack of validation won't block people
  from using the site

