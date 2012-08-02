# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):

    def forwards(self, orm):
        try:
            # Adding field 'User.is_fake'
            db.add_column(
                u'auth_user', 'is_fake',
                self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)
        except:
            pass

    def backwards(self, orm):
        db.delete_column('auth_user', 'is_fake')

    complete_apps = ['askbot']
