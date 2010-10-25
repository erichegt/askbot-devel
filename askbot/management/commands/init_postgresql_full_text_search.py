from django.core.management.base import NoArgsCommand
from django.db import connection
import os.path

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        
        dir = os.path.dirname(__file__)
        sql_file_name = 'setup_postgresql_full_text_search.plsql'
        sql_file_name = os.path.join(dir, sql_file_name)
        query = open(sql_file_name).read()

        cursor = connection.cursor()
        try:
            cursor.execute(query)
        finally:
            cursor.close()
