from django.core.management.base import BaseCommand
import os
import re
import sys
import stackexchange.parse_models as se_parser
from xml.etree import ElementTree as et
from django.db import models
import forum.models as osqa
import stackexchange.models as se
from forum.forms import EditUserEmailFeedsForm
from django.conf import settings

xml_read_order = (
        'VoteTypes','UserTypes','Users','Users2Votes',
        'Badges','Users2Badges','CloseReasons','FlatPages',
        'MessageTypes','PostHistoryTypes','PostTypes','SchemaVersion',
        'Settings','SystemMessages','ThemeResources','ThemeTextResources',
        'ThrottleBucket','UserHistoryTypes','UserHistory',
        'Users2Badges','VoteTypes','Users2Votes','MessageTypes',
        'Posts','Posts2Votes','PostHistory','PostComments',
        'ModeratorMessages','Messages','Comments2Votes',
        )

#association tables SE item id --> OSQA item id
#table associations are implied
USER = {}#SE User.id --> django(OSQA) User.id
NAMESAKE_COUNT = {}# number of times user name was used - for X.get_screen_name

class X(object):#
    """class with methods for handling some details
    of SE --> OSQA mapping
    """
    badge_type_map = {'1':'gold','2':'silver','3':'bronze'}

    osqa_supported_id_providers = (
            'google','yahoo','aol','myopenid',
            'flickr','technorati',#todo: typo in code openidauth/authentication.py !
            'wordpress','blogger','livejournal',
            'claimid','vidoop','verisign',
            'openidurl','facebook','local',
            'twitter' #oauth is not on this list, b/c it has no own url
            )

    @classmethod
    def get_screen_name(cls, name):
        """always returns unique screen name
        even if there are multiple users in SE 
        with the same exact screen name
        """
        if name is None:
            name = 'anonymous'
        name = name.strip()
        name = re.subn(r'\s+',' ',name)[0]#remove repeating spaces
        
        try:
            u = osqa.User.objects.get(username = name)
            try:
                if u.location:
                    name += ', %s' % u.location
                if name in NAMESAKE_COUNT:
                    NAMESAKE_COUNT[name] += 1
                    name += ' %d' % NAMESAKE_COUNT[name]
                else:
                    NAMESAKE_COUNT[name] = 1
            except osqa.User.DoesNotExist:
                pass
        except osqa.User.DoesNotExist:
            NAMESAKE_COUNT[name] = 1
        return name

    @classmethod
    def get_email(cls, email):#todo: fix fringe case - user did not give email!
        if email is None:
            return settings.ANONYMOUS_USER_EMAIL
        else:
            assert(email != '')
            return email

    #crude method of getting id provider name from the url
    @classmethod
    def get_openid_provider_name(cls, openid_url):
        openid_str = str(openid_url)
        bits = openid_str.split('/')
        base_url = bits[2] #assume this is base url
        url_bits = base_url.split('.')
        provider_name = url_bits[-2].lower()
        if provider_name not in cls.osqa_supported_id_providers:
            raise Exception('could not determine login provider for %s' % openid_url)
        return provider_name

    @staticmethod
    def blankable(input):
        if input is None:
            return ''
        else:
            return input

    @classmethod
    def parse_badge_summary(cls, badge_summary):
        (gold,silver,bronze) = (0,0,0)
        if badge_summary: 
            if len(badge_summary) > 3:
                print 'warning: guessing that badge summary is comma separated'
                print 'have %s' % badge_summary
                bits = badge_summary.split(',')
            else:
                bits = [badge_summary]
            for bit in bits:
                m = re.search(r'^(?P<type>[1-3])=(?P<count>\d+)$', bit)
                if not m:
                    raise Exception('could not parse badge summary: %s' % badge_summary)
                else:
                    badge_type = cls.badge_type_map[m.groupdict()['type']]
                    locals()[badge_type] = int(m.groupdict()['count'])
        return (gold,silver,bronze)

class Command(BaseCommand):
    help = 'Loads StackExchange data from unzipped directory of XML files into the OSQA database'
    args = 'se_dump_dir'

    def handle(self, *arg, **kwarg):
        if len(arg) < 1 or not os.path.isdir(arg[0]):
            print 'Error: first argument must be a directory with all the SE *.xml files'
            sys.exit(1)

        self.dump_path = arg[0]
        #read the data into SE tables
        for xml in xml_read_order:
            xml_path = self.get_xml_path(xml)
            table_name = self.get_table_name(xml)
            self.load_xml_file(xml_path, table_name)

        #transfer data into OSQA tables
        self.transfer_users()

    def load_xml_file(self, xml_path, table_name):
        tree = et.parse(xml_path)
        print 'loading from %s to %s' % (xml_path, table_name) ,
        model = models.get_model('stackexchange', table_name)
        i = 0
        for row in tree.findall('.//row'):
            model_entry = model()
            i += 1
            for col in row.getchildren():
                field_name = se_parser.parse_field_name(col.tag)
                field_type = model._meta.get_field(field_name)
                field_value = se_parser.parse_value(col.text, field_type)
                setattr(model_entry, field_name, field_value)
            model_entry.save()
        print '... %d objects saved' % i

    def get_table_name(self,xml):
        return se_parser.get_table_name(xml)

    def get_xml_path(self, xml):
        xml_path = os.path.join(self.dump_path, xml + '.xml') 
        if not os.path.isfile(xml_path):
            print 'Error: file %s not found' % xml_path
            sys.exit(1)
        return xml_path

    def transfer_users(self):
        for se_u in se.User.objects.all():
            if se_u.id < 1:#skip the Community user
                continue
            u = osqa.User()
            u_type = se_u.user_type.name
            if u_type == 'Administrator':
                u.is_superuser = True
            elif u_type == 'Moderator':
                u.is_staff = True
            elif u_type not in ('Unregistered', 'Registered'):
                raise Exception('unknown user type %s' % u_type)

            #if user is not registered, no association record created
            #we do not allow posting by users who are not authenticated
            #probably they'll just have to "recover" their account by email
            if u_type != 'Unregistered':
                assert(se_u.open_id)#everybody must have open_id
                u_auth = osqa.AuthKeyUserAssociation()
                u_auth.key = se_u.open_id
                u_auth.provider = X.get_openid_provider_name(se_u.open_id)
                u_auth.added_at = se_u.creation_date

            if se_u.open_id is None and se_u.email is None:
                print 'Warning: SE user %d is not recoverable (no email or openid)'

            u.reputation = se_u.reputation
            u.last_seen = se_u.last_access_date
            u.email = X.get_email(se_u.email)
            u.location = X.blankable(se_u.location)
            u.date_of_birth = se_u.birthday #dattime -> date
            u.website = X.blankable(se_u.website_url)
            u.about = X.blankable(se_u.about_me)
            u.last_login = se_u.last_login_date
            u.date_joined = se_u.creation_date
            u.is_active = True #todo: this may not be the case

            u.username = X.get_screen_name(se_u.display_name)
            u.real_name = X.blankable(se_u.real_name)

            (gold,silver,bronze) = X.parse_badge_summary(se_u.badge_summary)
            u.gold = gold
            u.silver = silver
            u.bronze = bronze

            #todo: we don't have these fields
            #views - number of profile views?
            #has_replies
            #has_message
            #opt_in_recruit
            #last_login_ip
            #open_id_alt - ??
            #preferences_raw - not clear how to use
            #display_name_cleaned - lowercased, srtipped name
            #timed_penalty_date
            #phone

            #don't know how to handle these - there was no usage example
            #password_id
            #guid

            #ignored
            #last_email_date - this translates directly to EmailFeedSetting.reported_at

            #save the data
            u.save()
            form = EditUserEmailFeedsForm()
            form.reset()
            if se_u.opt_in_email == True:#set up daily subscription on "own" items
                form.initial['individually_selected'] = 'd'
                form.initial['asked_by_me'] = 'd'
                form.initial['answered_by_me'] = 'd'
            #
            form.save(user=u, save_unbound=True)

            if 'u_auth' in locals():
                u_auth.user = u
                u_auth.save()
            USER[se_u.id] = u.id
