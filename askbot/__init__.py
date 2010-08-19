"""
:synopsis: the Django Q&A forum application
"""
import os

def get_install_directory():
    return os.path.dirname(__file__)

def get_version():
    return '0.6.9'
