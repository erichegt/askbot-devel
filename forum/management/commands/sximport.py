from django.core.management.base import LabelCommand
from zipfile import ZipFile
from xml.dom import minidom as dom
import datetime

from forum.models import User

class Command(LabelCommand):
    def handle_label(self, label, **options):
        zip = ZipFile(label)

        map = {}

        map['users'] = self.import_users(zip.open("Users.xml"))
        map['questions'], map['answers'] = self.import_posts(zip.open("Posts.xml"))


    def row_to_dic(self, row):
        return dict([
            (child.localName.lower(),
            " ".join([t.nodeValue for t in child.childNodes if t.nodeType == t.TEXT_NODE]))
            for child in row.childNodes
            if child.nodeType == child.ELEMENT_NODE
        ])

    def from_sx_time(self, timestring):
        if timestring is None:
            return timestring

        try:
            return datetime.datetime.strptime(timestring, '%Y-%m-%dT%H:%M:%S')
        except:
            return datetime.datetime.strptime(timestring, '%Y-%m-%dT%H:%M:%S.%f')


    def import_users(self, users):
        pkey_map = {}
        doc = dom.parse(users)

        rows = doc.getElementsByTagName('row')
        unknown_count = 0

        added_names = []

        for row in rows:
            values = self.row_to_dic(row)

            username = values.get('displayname',
                            values.get('realname',
                                values.get('email', None)))

            if username is None:
                unknown_count += 1
                username = 'Unknown User %d' % unknown_count

            if username in added_names:
                cnt = 1
                new_username = "%s %d" % (username, cnt)
                while new_username in added_names:
                    cnt += 1
                    new_username = "%s %d" % (username, cnt)

                username = new_username

            added_names.append(username)

            user = User(username=username, email=values.get('email', ''))

            user.reputation = values['reputation']
            user.last_seen = self.from_sx_time(values['lastaccessdate'])

            user.real_name = values.get('realname', '')
            user.about = values.get('aboutme', '')
            user.website = values.get('websiteurl', '')
            user.date_of_birth = self.from_sx_time(values.get('birthday', None))
            user.location = values.get('location', '')

            user.is_active = True
            user.email_isvalid = True


            if int(values['usertypeid']) == 5:
                user.is_superuser = True

            if int(values['usertypeid']) == 5:
                user.is_staff = True

            user.save()

            pkey_map[values['id']] = user

        return users

    def import_posts(self, posts, map):
        pkey_map = {}
        doc = dom.parse(posts)

        rows = doc.getElementsByTagName('row')

        for row in rows:
            map = {
                'title': row['']    
            }

            pass
        pass
            
        
        
