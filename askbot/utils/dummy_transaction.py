"""Dummy transaction module, use instead of :mod:`django.db.transaction`
when you want to debug code that would normally run under transaction management.
Usage::

    from askbot.utils import dummy_transaction as transaction

    @transaction.commit_manually
    def do_something():
        #your code making changes to the database
        transaction.commit()
        return
"""
import functools

def commit_manually(func):
    """fake ``commit_manually`` decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def commit():
    """fake transaction commit"""
    pass
