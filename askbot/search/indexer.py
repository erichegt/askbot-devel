from django.conf import settings
from django.db import connection

def create_fulltext_indexes():
    if settings.DATABASE_ENGINE == 'mysql':
        cursor = connection.cursor()
        cursor.execute('ALTER TABLE question ADD FULLTEXT (title, text, tagnames)')
        cursor.execute('ALTER TABLE answer ADD FULLTEXT (title, text, tagnames)')

