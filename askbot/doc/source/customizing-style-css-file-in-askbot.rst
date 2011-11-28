.. _customizing-style-css-file-in-askbot:

====================================
Customizing style.css file in Askbot
====================================

File style.css is produced by the `lesscss compiler <http://lesscss.org>`_ - ``lessc``.

Please read documentation about the lesscss format.

Compiling lesscss files
=======================

The following command will compile the lesscss source file,
an option -x will produce compressed css file:

    lessc file.lesscss -x > file.css

Installing lesscss
==================

Make sure you have recent version of `node.js <http://nodejs.org>`_ - latest version preferred.
More recent versions of node come with the tool called `npm <http://npmjs.org>`_,
for earlier versions ``npm`` will need to be installed manually.

To install lesscss, type:

    sudo npm install less
