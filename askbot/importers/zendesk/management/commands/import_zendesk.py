"""importer from cnprog, please note, that you need an exporter in the first place
to use this command.
If you are interested to use it - please ask Evgeny <evgeny.fadeev@gmail.com>
"""
import os
import re
import sys
import tarfile
import tempfile
from datetime import datetime, date
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from lxml import etree
from askbot import models as askbot_models
from askbot.utils import console
from askbot.utils.html import unescape

from askbot.importers.zendesk import models as zendesk_models

#a hack, did not know how to parse timezone offset
ZERO_TIME = datetime.strptime('00:00', '%H:%M')

def get_unique_username(name_seed):
    """returns unique user name, by modifying the
    name if the same name exists in the database
    until the modified name is unique
    """
    original_name = name_seed
    attempt_no = 1
    while True:
        try:
            askbot_models.User.objects.get(username = name_seed)
            name_seed = original_name + str(attempt_no)
            attempt_no += 1
        except askbot_models.User.DoesNotExist:
            return name_seed

def clean_username(name_seed):
    """makes sure that the name is unique
    and is no longer than 30 characters"""
    username = get_unique_username(name_seed)
    if len(username) > 30:
        username = get_unique_username(username[:28])
        if len(username) > 30:
            #will allow about a million extra possible unique names
            username = get_unique_username(username[:24])
    return username

def get_val(elem, field_name):
    field = elem.find(field_name)
    if field is None:
        return None
    try:
        field_type = field.attrib['type']
    except KeyError:
        field_type = ''
    raw_val = field.text
    if raw_val is None:
        return None

    if field_type == 'boolean':
        if raw_val == 'true':
            return True
        elif raw_val == 'false':
            return False
        else:
            raise ValueError('"true" or "false" expected, found "%s"' % raw_val)
    elif field_type.endswith('integer'):
        return int(raw_val)
    elif field_type == 'datetime':
        if raw_val is None:
            return None
        raw_datetime = raw_val[:19]
        tzoffset_sign = raw_val[19]
        raw_tzoffset = raw_val[20:]
        if raw_val:
            dt = datetime.strptime(raw_datetime, '%Y-%m-%dT%H:%M:%S')
            tzoffset_amt = datetime.strptime(raw_tzoffset, '%H:%M')
            tzoffset = tzoffset_amt - ZERO_TIME
            if tzoffset_sign == '-':
                return dt - tzoffset
            else:
                return dt + tzoffset
        else:
            return None
    else:
        return raw_val

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise CommandError('please provide path to tarred and gzipped cnprog dump')

        self.tar = tarfile.open(args[0], 'r:gz')

        sys.stdout.write('Reading users.xml: ')
        self.read_users()
        sys.stdout.write('Reading posts.xml: ')
        self.read_posts()
        sys.stdout.write('Reading forums.xml: ')
        self.read_forums()
        
        sys.stdout.write("Importing user accounts: ")
        self.import_users()
        #self.import_openid_associations()
        #self.import_content()

    def get_file(self, file_name):
        first_item = self.tar.getnames()[0]
        file_path = file_name
        if not first_item.endswith('.xml'):
            file_path = os.path.join(first_item, file_path)
            
        file_info = self.tar.getmember(file_path)
        xml_file = self.tar.extractfile(file_info)
        return etree.parse(xml_file)

    @transaction.commit_manually
    def read_xml_file(self,
            file_name = None,
            entry_name = None,
            model = None,
            fields = None,
            extra_field_mappings = None
        ):
        """
        * file_name - is name of xml file,
        * entry_name - name of entries to read from the xml file
        * model - model, which is to receive data
        * fields - list of field names in xml that will be translated to model fields
                   by simple substitiution of '-' with '_'
        * extra field mappings - list of two tuples where xml field names are
          translated to model fields in a special way
        """
        xml = self.get_file(file_name)
        items_saved = 0
        for xml_entry in xml.findall(entry_name):
            instance = model()
            for field in fields:
                value = get_val(xml_entry, field)
                model_field_name = field.replace('-', '_')
                setattr(instance, model_field_name, value)
            if extra_field_mappings:
                for (field, model_field_name) in extra_field_mappings:
                    value = get_val(xml_entry, field)
                    setattr(instance, model_field_name, value)
            instance.save()
            transaction.commit()
            items_saved += 1
            console.print_action('%d items' % items_saved)
        console.print_action('%d items' % items_saved, nowipe = True)


    def read_users(self):
        self.read_xml_file(
            file_name = 'users.xml',
            entry_name = 'user',
            model = zendesk_models.User,
            fields = (
                'created-at', 'is-active', 'last-login', 'name',
                'openid-url', 'organization-id', 'phone', 'restriction-id',
                'roles', 'time-zone', 'updated-at', 'uses-12-hour-clock',
                'email', 'is-verified', 'photo-url'
            ),
            extra_field_mappings = (('id', 'user_id'),)
        )

    def read_posts(self):
        self.read_xml_file(
            file_name = 'posts.xml',
            entry_name = 'post',
            model = zendesk_models.Post,
            fields = (
                'body', 'created-at', 'updated-at', 'entry-id',
                'forum-id', 'user-id', 'is-informative'
            ),
        )

    def read_forums(self):
        self.read_xml_file(
            file_name = 'forums.xml',
            entry_name = 'forum',
            model = zendesk_models.Forum,
            fields = (
                'description', 'display-type-id',
                'entries-count', 'is-locked',
                'name', 'organization-id',
                'position', 'updated-at',
                'translation-locale-id',
                'use-for-suggestions',
                'visibility-restriction-id',
                'is-public'
            ),
            extra_field_mappings = (('id', 'forum_id'),)
        )

    @transaction.commit_manually
    def import_users(self):
        added_users = 0
        for zd_user in zendesk_models.User.objects.all():
            #a whole bunch of fields are actually dropped now
            #see what's available in users.xml meanings of some
            #values there is not clear
            try:
                ab_user = askbot_models.User.objects.get(email = zd_user.email)
            except askbot_models.User.DoesNotExist:
                #special treatment for the user name
                raw_username = unescape(zd_user.name)
                username = clean_username(raw_username)
                if len(username) > 30:#nearly impossible skip such user
                    print "Warning: could not import user %s" % raw_username
                    continue

                if zd_user.email is None:
                    email = ''
                else:
                    email = zd_user.email

                ab_user = askbot_models.User(
                    email = email,
                    email_isvalid = zd_user.is_verified,
                    date_joined = zd_user.created_at,
                    last_seen = zd_user.created_at,#add initial date for now
                    username = username,
                    is_active = zd_user.is_active
                )
                ab_user.save()
                added_users += 1
                console.print_action(ab_user.username)
            zd_user.askbot_user_id = ab_user.id
            zd_user.save()
            transaction.commit()
        console.print_action('%d users added' % added_users, nowipe = True)

    def import_content(self):
        for zd_post in zendesk_models.Post.objects.all():
            if zd_post.is_processed:
                continue
