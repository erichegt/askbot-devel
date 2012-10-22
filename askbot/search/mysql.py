"""Utilities for the MySQL backend"""
from django.db import connection

NO_FTS_WARNING = """
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!                                                  !!
!!  WARNING: Your database engine does not support  !!
!!  full text search. Please switch to PostgresQL   !!
!!  or select MyISAM engine for MySQL               !!
!!                                                  !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""
SUPPORTS_FTS = None

def supports_full_text_search():
    """True if the database engine is MyISAM"""
    from askbot.models import Post
    global SUPPORTS_FTS
    if SUPPORTS_FTS is None:
        cursor = connection.cursor()
        table_name = Post._meta.db_table
        cursor.execute("SHOW CREATE TABLE %s" % table_name)
        data = cursor.fetchone()
        if 'ENGINE=MyISAM' in data[1]:
            SUPPORTS_FTS = True
        else:
            SUPPORTS_FTS = False
    return SUPPORTS_FTS

def get_create_full_text_index_sql(index_name, table_name, column_list):
    cursor = connection.cursor()
    column_sql = '(%s)' % ','.join(column_list)
    sql = 'CREATE FULLTEXT INDEX %s on %s %s' % (index_name, table_name, column_sql)
    cursor.execute(sql)
    return sql

def get_drop_index_sql(index_name, table_name):
    return 'ALTER TABLE %s DROP INDEX %s' % (table_name, index_name)

