"""
:synopsis: the Django Q&A forum application

Functions in the askbot module perform various
basic actions on behalf of the forum application
"""
import os
import smtplib
import sys
import logging
from askbot import patches
from askbot.deployment.assertions import assert_package_compatibility

VERSION = (0, 6, 75)

#necessary for interoperability of django and coffin
assert_package_compatibility()
patches.patch_django()
patches.patch_coffin()#must go after django

def get_install_directory():
    """returns path to directory
    where code of the askbot django application 
    is installed
    """
    return os.path.dirname(__file__)


def get_version():
    """returns version of the askbot app
    this version is meaningful for pypi only
    """
    return '.'.join([str(subversion) for subversion in VERSION])
