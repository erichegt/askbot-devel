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
from askbot import models
from askbot.utils import console
from askbot.utils.html import unescape

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
            models.User.objects.get(username = name_seed)
            name_seed = original_name + str(attempt_no)
            attempt_no += 1
        except models.User.DoesNotExist:
            return name_seed

def get_val(elem, field_name):
    field = elem.find(field_name)
    try:
        field_type = field.attrib['type']
    except KeyError:
        field_type = ''
    raw_val = field.text
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
        if raw_val:
            return raw_val
        else:
            return ''

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise CommandError('please provide path to tarred and gzipped cnprog dump')

        self.tar = tarfile.open(args[0], 'r:gz')
        
        sys.stdout.write("Importing user accounts: ")
        self.import_users()
        #self.import_openid_associations()
        #self.import_email_settings()

        #self.import_question_edits()
        #self.import_answer_edits()

        #self.import_question_data()
        #self.import_answer_data()

        #self.import_comments()

        #self.import_question_views()
        #self.import_favorite_questions()
        #self.import_marked_tags()

        #self.import_votes()

    def get_file(self, file_name):
        first_item = self.tar.getnames()[0]
        file_path = file_name
        if not first_item.endswith('.xml'):
            file_path = os.path.join(first_item, file_path)
            
        file_info = self.tar.getmember(file_path)
        xml_file = self.tar.extractfile(file_info)
        return etree.parse(xml_file)

    @transaction.commit_manually
    def import_users(self):
        xml = self.get_file('users.xml')
        added_users = 0
        for user in xml.findall('user'):
            #a whole bunch of fields are actually dropped now
            #see what's available in users.xml meanings of some
            #values there is not clear

            #special treatment for the user name
            username = unescape(get_val(user, 'name'))#unescape html entities
            username = get_unique_username(username)

            ab_user = models.User(
                email = get_val(user, 'email'),
                email_isvalid = get_val(user, 'is-verified'),
                date_joined = get_val(user, 'created-at'),
                username = username,
                is_active = get_val(user, 'is-active'),
            )
            ab_user.save()
            added_users += 1
            console.print_action(ab_user.username)
            transaction.commit()
        console.print_action('%d users added' % added_users, nowipe = True)
        transaction.commit()
