# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'GroupMembership', fields ['group', 'user']
        db.delete_unique('askbot_groupmembership', ['group_id', 'user_id'])

        # Removing unique constraint on 'PostToGroup', fields ['post', 'tag']
        db.delete_unique('askbot_post_groups_old', ['post_id', 'tag_id'])
        # Removing M2M table for field groups on 'Post'
        db.delete_table('askbot_post_groups_old')

        # Deleting model 'GroupProfile'
        db.delete_table('askbot_groupprofile')

        # Deleting model 'GroupMembership'
        db.delete_table('askbot_groupmembership')

        # Removing M2M table for field new_groups on 'Thread'
        db.delete_unique('askbot_thread_groups_old', ['thread_id', 'tag_id'])
        db.delete_table('askbot_thread_groups_old')

    def backwards(self, orm):
        # Adding model 'GroupProfile'
        db.create_table('askbot_groupprofile', (
            ('preapproved_emails', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('is_open', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('preapproved_email_domains', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('moderate_email', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('logo_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('group_tag', self.gf('django.db.models.fields.related.OneToOneField')(related_name='group_profile', unique=True, to=orm['askbot.Tag'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('askbot', ['GroupProfile'])

        # Adding model 'GroupMembership'
        db.create_table('askbot_groupmembership', (
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_memberships', to=orm['askbot.Tag'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='group_memberships', to=orm['auth.User'])),
        ))
        db.send_create_signal('askbot', ['GroupMembership'])

        # Adding unique constraint on 'GroupMembership', fields ['group', 'user']
        db.create_unique('askbot_groupmembership', ['group_id', 'user_id'])

        # Adding M2M table for field groups on 'Post'
        db.create_table('askbot_post_groups_old', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm['askbot.post'], null=False)),
            ('tag', models.ForeignKey(orm['askbot.tag'], null=False))
        ))
        db.create_unique('askbot_post_groups_old', ['post_id', 'tag_id'])

        # Adding M2M table for field new_groups on 'Thread'
        db.create_table('askbot_thread_groups_old', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('thread', models.ForeignKey(orm['askbot.thread'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('askbot_thread_groups_old', ['thread_id', 'group_id'])

    complete_apps = ['askbot']
