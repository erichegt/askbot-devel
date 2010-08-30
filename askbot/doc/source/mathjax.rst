.. _mathjax:

===================
Installing MathJax
===================

MathJax_ is a browser independent javascript rendering engine for mathematical
expressions. On a MathJax-enabled site, such as Askbot :) you can display
perfectly formatted mathematical formulae.

However, MathJax distribution is very large and because of the size is not
shipped with Askbot.

To enable MathJax on your site, three things need to be done:

* download MathJax to some directory on your server
* edit webserver configuration so that url `http://example.com/mathjax`
  points to that directory and file `MathJax.js` is available at 
  `http://example.com/mathjax/MathJax.js`. For Apache, a following line 
  in the apache configuration file (maybe a VirtualHost section) will do::

  Alias /mathjax/ /filesystem/path/to/mathjax/

* in Askbot "settings" -> "Optional components", check "Enable MathJax" and
  enter url `http://example.com/mathjax`

Note: your actual forum site must in this case be available at `http://example.com`.
It is **very important** to serve MathJax media **from the same domain**, otherwise
mathematics rendering will be very slow in Firefox and some other browsers (those 
using the "same origin" policy for the HTTP cookies - MathJax does use sookies to
store some Math display settings)

One day enabling MathJax will be even easier, but `some more work`_ needs to be done for this to happen.

.. _MathJax: http://mathjax.org
.. _`some more work`: http://bugs.askbot.org/issues/27
