"""this module serves as a helper for the South orm
by mitigating absence of access to the django model api

since models change with time, this api is implemented in different
versions. Different versions do not need to have all the same functions.
"""
from south.db import db

def safe_add_column(table, column, column_data, keep_default = False):
    """when user calls syncdb with askbot the first time
    the auth_user table will be created together with the patched columns
    so, we need to add these columns here in separate transactions
    and roll back if they fail, if we want we could also record - which columns clash
    """
    try:
        db.start_transaction()
        db.add_column(table, column, column_data, keep_default = keep_default)
        db.commit_transaction()
        return True
    except:
        db.rollback_transaction()
        return False


class BaseAPI(object):
    def __init__(self, orm):
        self.orm = orm
