# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

table_prefix = u'nmrwiki'
from django.db import models
import re
from django.conf import settings
import logging
from django.contrib.auth.models import User as DjangoUser
from django.utils.translation import ugettext as _
import hashlib
import time
import random

MW_TS = '%Y%m%d%H%M%S'

TITLE_CHOICES = (
    ('none',_('----')),
    ('prof',_('Prof.')),
    ('dr',_('Dr.')),
)

class User(models.Model):
    user_id = models.IntegerField(primary_key=True,db_column='user_id')
    user_name = models.CharField(max_length=765)
    user_real_name = models.CharField(max_length=765)
    user_password = models.TextField()
    user_newpassword = models.TextField()
    user_newpass_time = models.CharField(max_length=14, blank=True)
    user_email = models.TextField()
    user_options = models.TextField()
    user_touched = models.CharField(max_length=14)
    user_token = models.CharField(max_length=32)
    user_email_authenticated = models.CharField(max_length=14, blank=True)
    user_email_token = models.CharField(max_length=32, blank=True)
    user_email_token_expires = models.CharField(max_length=14, blank=True)
    user_registration = models.CharField(max_length=14, blank=True)
    user_editcount = models.IntegerField(null=True, blank=True)
    user_last_name = models.CharField(max_length=765, blank=True)
    user_first_name = models.CharField(max_length=765, blank=True)
    user_reason_to_join = models.CharField(max_length=765, blank=True)
    user_title = models.CharField(max_length=16, blank=True, choices=TITLE_CHOICES)
    class Meta:
        db_table = table_prefix + u'user'
        managed = False

    def set_default_options(self):
        default_options = {
            'quickbar':1,
            'underline':2,
            'cols':80,
            'rows':25,
            'searchlimit':20,
            'contextlines':5,
            'contextchars':50,
            'skin':'false',
            'math':1,
            'rcdays':7,
            'rclimit':50,
            'wllimit':250,
            'highlightbroken':1,
            'stubthreshold':0,
            'previewontop':1,
            'editsection':1,
            'editsectiononrightclick':0,
            'showtoc':1,
            'showtoolbar':1,
            'date':'default',
            'imagesize':2,
            'thumbsize':2,
            'rememberpassword':0,
            'enotifwatchlistpages':0,
            'enotifusertalkpages':1,
            'enotifminoredits':0,
            'enotifrevealaddr':0,
            'shownumberswatching':1,
            'fancysig':0,
            'externaleditor':0,
            'externaldiff':0,
            'showjumplinks':1,
            'numberheadings':0,
            'uselivepreview':0,
            'watchlistdays':3.0,
            'usenewrc':1,
        }
        self.user_options = '\n'.join( 
                                        map(lambda opt: '%s=%s' % (opt[0], str(opt[1])), 
                                            default_options.items())
                                     )

    def set_password_and_token(self,password):
        p = hashlib.md5(password).hexdigest()
        if hasattr(settings,'MEDIAWIKI_SALT_PASSWORD') and settings.MEDIAWIKI_SALT_PASSWORD == True:
            p = hashlib.md5('%d-%s' % (self.user_id, p)).hexdigest()
        self.user_password = p
        self.user_token = hashlib.md5(p + str(time.time())).hexdigest()

    def get_name(self):
        if self.user_real_name:
            if re.search(r'\S',self.user_real_name):
                return self.user_real_name
        return self.user_name + ' (nickname)'

    def get_html(self):
        return '<a href="%s">%s</a>' % (self.get_absolute_url(),self.get_name())

    def get_absolute_url(self):
        url = settings.MEDIAWIKI_URL + '?title=User:' + self.user_name
        return url

class UserProfile(models.Model):
    nup_user_id = models.ForeignKey(User,primary_key=True,db_column='nup_user_id')
    nup_about = models.CharField(max_length=765, blank=True)
    nup_position_title = models.CharField(max_length=765, blank=True)
    nup_position_type = models.CharField(max_length=765, blank=True)
    nup_employer_division = models.CharField(max_length=765, blank=True)
    nup_employer_company = models.CharField(max_length=765, blank=True)
    nup_employer_type = models.CharField(max_length=765, blank=True)
    nup_employment_status = models.CharField(max_length=45, blank=True)
    nup_profession = models.CharField(max_length=765, blank=True)
    nup_city = models.CharField(max_length=765, blank=True)
    nup_state = models.CharField(max_length=765, blank=True)
    nup_country = models.CharField(max_length=765, blank=True)
    nup_lattitude = models.FloatField(null=True, blank=True)
    nup_longitude = models.FloatField(null=True, blank=True)
    nup_hiring = models.IntegerField(null=True, blank=True)
    nup_hunting = models.IntegerField(null=True, blank=True)
    nup_education = models.TextField(blank=True)
    nup_websites = models.TextField(blank=True)
    nup_interests = models.TextField(blank=True)
    nup_job_ad = models.TextField(blank=True)
    nup_job_ad_title = models.CharField(max_length=765, blank=True)
    nup_job_ad_active = models.IntegerField(null=True, blank=True)
    nup_expertise = models.TextField(blank=True)
    nup_is_approved = models.BooleanField()
    class Meta:
        db_table = table_prefix + u'new_user_profile'
        managed = False

class RecentChanges(models.Model):
    rc_id = models.AutoField(primary_key=True, db_column='rc_id')
    rc_timestamp = models.CharField(max_length=14)
    rc_cur_time = models.CharField(max_length=14)
    rc_user = models.ForeignKey(User, db_column='rc_user')
    rc_user_text = models.CharField(max_length=765)
    rc_namespace = models.IntegerField()
    rc_title = models.CharField(max_length=765)
    rc_comment = models.CharField(max_length=765)
    rc_minor = models.IntegerField()
    rc_bot = models.IntegerField()
    rc_new = models.IntegerField()
    rc_cur_id = models.IntegerField()
    rc_this_oldid = models.IntegerField()
    rc_last_oldid = models.IntegerField()
    rc_type = models.IntegerField()
    rc_moved_to_ns = models.IntegerField()
    rc_moved_to_title = models.CharField(max_length=765)
    rc_patrolled = models.IntegerField()
    rc_ip = models.CharField(max_length=40)
    rc_old_len = models.IntegerField(null=True, blank=True)
    rc_new_len = models.IntegerField(null=True, blank=True)
    rc_deleted = models.IntegerField()
    rc_logid = models.ForeignKey('Logging', db_column='rc_logid')
    rc_log_type = models.CharField(max_length=255, blank=True)
    rc_log_action = models.CharField(max_length=255, blank=True)
    rc_params = models.TextField(blank=True)
    class Meta:
        db_table = table_prefix + u'recentchanges'
        managed = False

class Logging(models.Model):
    log_id = models.AutoField(primary_key=True)
    log_type = models.CharField(max_length=10)
    log_action = models.CharField(max_length=10)
    log_timestamp = models.CharField(max_length=14)
    log_user = models.ForeignKey(User,db_column='log_user')
    log_namespace = models.IntegerField()
    log_title = models.CharField(max_length=765)
    log_comment = models.CharField(max_length=765)
    log_params = models.TextField()
    log_deleted = models.IntegerField()
    class Meta:
        db_table = table_prefix + u'logging'
        managed = False

    def show_in_recent_changes(self, ip=None, rc_minor=False):
        #to call this method self object must already exist in DB
        if self.log_type == 'newusers' and self.log_action=='create':
            rc = RecentChanges(
                                rc_ip=ip,
                                rc_minor=int(rc_minor),
                                rc_deleted=0,
                                rc_bot=0,
                                rc_new=0,
                                rc_moved_to_title='',
                                rc_moved_to_ns=0,
                                rc_this_oldid=0,
                                rc_last_oldid=0,
                                rc_patrolled=1,
                                rc_old_len=None,
                                rc_new_len=None,
                                rc_logid=self,
                                rc_user=self.log_user,
                                rc_user_text=self.log_user.user_name,
                                rc_log_type=self.log_type,
                                rc_log_action=self.log_action,
                                rc_timestamp = self.log_timestamp,
                                rc_cur_time = self.log_timestamp,
                                rc_title='Log/newusers',
                                rc_namespace=-1, #-1 special, 2 is User namespace
                                rc_params=self.log_params,
                                rc_comment=_('Welcome new user!'),
                                rc_type=3,#MW RCLOG constant from Defines.php
                                rc_cur_id=0,
                            )
            rc.save()
        else:
            raise NotImplementedError()
        

class Page(models.Model):
    page_id = models.AutoField(primary_key=True)
    page_namespace = models.IntegerField(unique=True)
    page_title = models.CharField(max_length=765)
    page_restrictions = models.TextField()
    page_counter = models.IntegerField()
    page_is_redirect = models.IntegerField()
    page_is_new = models.IntegerField()
    page_random = models.FloatField()
    page_touched = models.CharField(max_length=14)
    page_latest = models.IntegerField()
    page_len = models.IntegerField()
    class Meta:
        db_table = table_prefix + u'page'
        managed = False
    def save(self):
        raise Exception('WikiUser table is read-only in this application')

class PageLinks(models.Model):
    pl_from = models.ForeignKey(Page)
    pl_namespace = models.IntegerField()
    pl_title = models.CharField(max_length=765)
    class Meta:
        db_table = table_prefix + u'pagelinks'
        managed = False
    def save(self):
        raise Exception('WikiUser table is read-only in this application')

class Revision(models.Model):
    rev_id = models.IntegerField(unique=True)
    rev_page = models.IntegerField()
    rev_text_id = models.IntegerField()
    rev_comment = models.TextField()
    rev_user = models.IntegerField()
    rev_user_text = models.CharField(max_length=765)
    rev_timestamp = models.CharField(max_length=14)
    rev_minor_edit = models.IntegerField()
    rev_deleted = models.IntegerField()
    rev_len = models.IntegerField(null=True, blank=True)
    rev_parent_id = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = table_prefix + u'revision'
        managed = False

class Text(models.Model):
    old_id = models.IntegerField(primary_key=True)
    old_text = models.TextField()
    old_flags = models.TextField()
    class Meta:
        db_table = table_prefix + u'text'
        managed = False

#nmrwiki_stats table may be of interest

class UserGroups(models.Model):
    ug_user = models.ForeignKey(User,primary_key=True)
    ug_group = models.CharField(max_length=16)
    class Meta:
        db_table = table_prefix + u'user_groups'
        managed = False

def user_get_absolute_url(user):
    return user.mediawiki_user.get_absolute_url()

def user_get_html(user):
    return user.mediawiki_user.get_html()

def user_has_valid_email(user):
    if user.mediawiki_user.user_email_authenticated:
        return True
    else:
        return False

def user_get_description_for_admin(user):
    out = user.get_html() + ' (%s)' % user.username
    if user.has_valid_email():
        out += ' - has valid email'
    else:
        out += ' - <em>no email!</em>'
    return out

DjangoUser.add_to_class('mediawiki_user',models.ForeignKey(User, null=True))
DjangoUser.add_to_class('get_wiki_profile_url',user_get_absolute_url)
DjangoUser.add_to_class('get_wiki_profile_url_html',user_get_html)
DjangoUser.add_to_class('get_description_for_admin',user_get_description_for_admin)
DjangoUser.add_to_class('has_valid_wiki_email',user_has_valid_email)
