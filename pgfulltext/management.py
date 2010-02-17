import os

from django.db import connection, transaction
from django.conf import settings

import forum.models

if settings.USE_PG_FTS:
    from django.db.models.signals import post_syncdb

    def setup_pgfulltext(sender, **kwargs):
        if sender == forum.models_:
           install_pg_fts()

    post_syncdb.connect(setup_pgfulltext)

def install_pg_fts():
    f = open(os.path.join(os.path.dirname(__file__), '../sql_scripts/pg_fts_install.sql'), 'r')
    cursor = connection.cursor()
    cursor.execute(f.read())
    transaction.commit_unless_managed()
    f.close()
    