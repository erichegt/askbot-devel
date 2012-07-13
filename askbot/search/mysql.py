from django.db import connection

SUPPORTS_FTS = None
HINT_TABLE = None
NO_FTS_WARNING = """
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!                                                  !!
!!  WARNING: Your database engine does not support  !!
!!  full text search. Please switch to PostgresQL   !!
!!  or select MyISAM engine for MySQL               !!
!!                                                  !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""

def supports_full_text_search(hint_table = None):
    """True if the database engine is MyISAM
    hint_table - is the table that we look into to determine
    whether database supports FTS or not.
    """
    global SUPPORTS_FTS
    global HINT_TABLE
    if SUPPORTS_FTS is None:
        cursor = connection.cursor()
        if hint_table:
            table_name = hint_table
            HINT_TABLE = hint_table
        else:
            from askbot.models import Post
            table_name = Post._meta.db_table
        cursor.execute("SHOW CREATE TABLE %s" % table_name)
        data = cursor.fetchone()
        if 'ENGINE=MyISAM' in data[1]:
            SUPPORTS_FTS = True
        else:
            SUPPORTS_FTS = False
    return SUPPORTS_FTS

                question_index_sql = get_create_full_text_index_sql(
                                                index_name,
                                                table_namee,
                                                ('title','text','tagnames',)
                                            )
def get_create_full_text_index_sql(index_name, table_name, column_list):
    cursor = connection.cursor()
    column_sql = '(%s)' % ','.join(column_list)
    sql = 'CREATE FULLTEXT INDEX %s on %s %s' % (index_name, table_name, column_sql)
    cursor.execute(question_index_sql)
    return sql
            else:
                print NO_FTS_WARNING

def get_drop_index_sql(index_name, table_name):
    return 'ALTER TABLE %s DROP INDEX %s' % (table_name, index_name)

