"""Utilities for the MySQL backend"""
from django.db import connection

#in-memory cached variable
SUPPORTS_FTS = None

def supports_full_text_search():
    """True if the database engine is MyISAM"""
    from askbot.models import Question
    global SUPPORTS_FTS
    if SUPPORTS_FTS is None:
        cursor = connection.cursor()
        table_name = Question._meta.db_table
        cursor.execute("SHOW CREATE TABLE %s" % table_name);
        data = cursor.fetchone()
        if 'ENGINE=MyISAM' in data[1]:
            SUPPORTS_FTS = True
        else:
            SUPPORTS_FTS = False
    return SUPPORTS_FTS
