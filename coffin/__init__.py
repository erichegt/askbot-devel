"""
Coffin
~~~~~~

`Coffin <http://www.github.com/dcramer/coffin>` is a package that resolves the
impedance mismatch between `Django <http://www.djangoproject.com/>` and `Jinja2
<http://jinja.pocoo.org/2/>` through various adapters. The aim is to use Coffin
as a drop-in replacement for Django's template system to whatever extent is
reasonable.

:copyright: 2008 by Christopher D. Leary
:license: BSD, see LICENSE for more details.
"""


__all__ = ('__version__', '__build__', '__docformat__', 'get_revision')
__version__ = (0, 3)
__docformat__ = 'restructuredtext en'

import os

def _get_git_revision(path):
    revision_file = os.path.join(path, 'refs', 'heads', 'master')
    if not os.path.exists(revision_file):
        return None
    fh = open(revision_file, 'r')
    try:
        return fh.read()
    finally:
        fh.close()

def get_revision():
    """
    :returns: Revision number of this branch/checkout, if available. None if
        no revision number can be determined.
    """
    package_dir = os.path.dirname(__file__)
    checkout_dir = os.path.normpath(os.path.join(package_dir, '..'))
    path = os.path.join(checkout_dir, '.git')
    if os.path.exists(path):
        return _get_git_revision(path)
    return None

__build__ = get_revision()
