"""this module serves as a helper for the South orm
by mitigating absence of access to the django model api

since models change with time, this api is implemented in different
versions. Different versions do not need to have all the same functions.
"""

class BaseAPI(object):
    def __init__(self, orm):
        self.orm = orm
