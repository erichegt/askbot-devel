import os

from django.db import connection, transaction
from django.conf import settings

import forum.models

if settings.DATABASE_ENGINE in ('postgresql_psycopg2', 'postgresql', ):
    from django.db.models.signals import post_syncdb

    def setup_pgfulltext(sender, **kwargs):
        if sender == forum.models:
           install_pg_fts()

    post_syncdb.connect(setup_pgfulltext)

def install_pg_fts():
    f = open(os.path.join(os.path.dirname(__file__), 'pg_fts_install.sql'), 'r')
    
    try:
        cursor = connection.cursor()
        cursor.execute(f.read())
        transaction.commit_unless_managed()
    except:
        pass
    finally:
        cursor.close()

    f.close()
