"""
:synopsis: the Django Q&A forum application

Functions in the askbot module perform various
basic actions on behalf of the forum application
"""
import os
import smtplib
import logging

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
    return '0.6.67'
