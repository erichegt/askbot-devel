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
from forum.utils.html import sanitize_html
from django.conf import settings
#from markdown2 import Markdown
#markdowner = Markdown(html4tags=True)

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
QUESTION = {}
ANSWER = {}
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

    #these modes cannot be mixed
    exclusive_revision_modes = (
        'initial','edit','lock','unlock',
        'migrate','close','reopen','merge',
    )

    revision_type_map = {
        'Initial Title':'initial',
        'Initial Body':'initial',
        'Initial Tags':'initial',
        'Edit Title':'edit',
        'Edit Body':'edit',
        'Edit Tags':'edit',
        'Rollback Title':'rollback',
        'Rollback Body':'rollback',
        'Rollback Tags':'rollback',
        'Post Closed':'close',
        'Post Reopened':'reopen',
        'Post Deleted':'delete',
        'Post Undeleted':'undelete',
        'Post Locked':'lock',
        'Post Unlocked':'unlock',
        'Community Owned':'wiki',
        'Post Migrated':'migrate',
        'Question Merged':'merge',
    }

    @classmethod
    def get_post_revision_group_types(cls, rev_group):
        rev_types = {} 
        for rev in rev_group:
            rev_type = cls.get_post_revision_type(rev)
            rev_types[rev_type] = 1
        rev_types = rev_types.keys()

        #make sure that exclusive rev modes are not mixed
        exclusive = cls.exclusive_revision_modes
        if len(rev_types) > 1 and all([t in exclusive for t in rev_types]):
            tstr = ','.join(rev_types)
            gstr = ','.join([str(rev.id) for rev in rev_group])
            msg = 'incompatible revision types %s in PostHistory %s' % (tstr,gstr)
            raise Exception(msg)
        return rev_types

    @classmethod
    def clean_tags(cls, tags):
        tags = re.subn(r'\s+',' ',tags.strip())[0]
        bits = tags.split(' ')
        tags = ' '.join([bit[1:-1] for bit in bits])
        tags = re.subn(r'\xf6','-',tags)[0]
        return tags

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

    @classmethod
    def get_post_revision_type(cls, rev):
        rev_name = rev.post_history_type.name
        rev_type = cls.revision_type_map.get(rev_name, None)
        if rev_type is None:
            raise Exception('dont understand revision type %s' % rev)
        return rev_type

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
        self.transfer_question_and_answer_activity()
        self.transfer_comments()
        self.transfer_badges()
        self.transfer_votes()
        self.transfer_favorites()
        self.transfer_update_subscriptions()
        self.transfer_flags()
        self.transfer_meta_pages()

    def _process_post_initial_revision_group(self, rev_group):

        title = None
        text = None
        tags = None
        wiki = False
        author = USER[rev_group[0].user.id]
        added_at = rev_group[0].creation_date

        for rev in rev_group:
            rev_type = rev.post_history_type.name
            if rev_type == 'Initial Title':
                title = rev.text
            elif rev_type == 'Initial Body':
                text = rev.text
            elif rev_type == 'Initial Tags':
                tags = X.clean_tags(rev.text)
            elif rev_type == 'Community Owned':
                wiki = True
            else:
                raise Exception('unexpected revision type %s' % rev_type)

        post_type = rev_group[0].post.post_type.name
        if post_type == 'Question':
            q = osqa.Question.objects.create_new(
                title            = title,
                author           = author,
                added_at         = added_at,
                wiki             = wiki,
                tagnames         = tags,
                text = text
            )
            QUESTION[rev_group[0].post.id] = q
        elif post_type == 'Answer':
            q = QUESTION[rev_group[0].post.parent.id]
            a = osqa.Answer.objects.create_new(
                question = q,
                author = author,
                added_at = added_at,
                wiki = wiki,
                text = text,
            )
            ANSWER[rev_group[0].post.id] = a
        else:
            post_id = rev_group[0].post.id
            raise Exception('unknown post type %s for id=%d' % (post_type, post_id))

    def _process_post_edit_revision_group(self, rev_group):
        #question apply edit
        (title, text, tags, wiki) = (None, None, None, False)
        for rev in rev_group:
            rev_type = rev.post_history_type.name
            if rev_type == 'Edit Title':
                title = rev.text
            elif rev_type == 'Edit Body':
                text = rev.text
            elif rev_type == 'Edit Tags':
                tags = X.clean_tags(rev.text)
            elif rev_type == 'Community Owned':
                wiki = True
            else:
                raise Exception('unexpected revision type %s' % rev_type)

        rev0 = rev_group[0]
        edited_by = USER[rev0.user.id]
        edited_at = rev0.creation_date
        comment = ';'.join([rev.comment for rev in rev_group if rev.comment])
        post_type = rev0.post.post_type.name

        if post_type == 'Question':
            q = QUESTION[rev0.post.id]
            q.apply_edit(
                edited_at = edited_at,
                edited_by = edited_by,
                title = title,
                text = text,
                comment = comment,
                tags = tags,
                wiki = wiki
            )
        elif post_type == 'Answer':
            a = ANSWER[rev0.post.id]
            #todo: wiki will probably be lost here
            a.apply_edit(
                edited_at = edited_at,
                edited_by = edited_by,
                text = text,
                comment = comment,
                wiki = wiki
            )

    def _process_post_action_revision_group(self, rev_group):
        pass

    def _process_post_revision_group(self, rev_group):
        #determine revision type
        rev_types = X.get_post_revision_group_types(rev_group) 
        #initial,edit,lock,unlock,
        #migrate,close,reopen,merge,wiki
        if 'initial' in rev_types:
            self._process_post_initial_revision_group(rev_group)
        elif 'edit' in rev_types:
            self._process_post_edit_revision_group(rev_group)
        else:
            self._process_post_action_revision_group(rev_group)

    def transfer_question_and_answer_activity(self):
        """transfers all question and answer
        edits and related status changes
        """
        #assuming that there are only two post types
        se_revs = se.PostHistory.objects.all()
        #assuming that chronologial order is correct and there
        #will be no problems of data integrity upon insertion of records
        se_revs = se_revs.order_by('creation_date','revision_guid')
        #todo: ignored fringe case - no revisions
        c_guid = se_revs[0].revision_guid
        c_group = []
        #this loop groups revisions by revision id, then calls process function
        #for the revision grup (elementary revisions posted at once)
        for se_rev in se_revs:
            if se_rev.revision_guid == c_guid:
                c_group.append(se_rev)
            else:
                self._process_post_revision_group(c_group)
                c_group = []
                c_group.append(se_rev)
                c_guid = se_rev.revision_guid

    def transfer_comments(self):
        pass

    def transfer_badges(self):
        pass

    def transfer_votes(self):
        pass

    def transfer_favorites(self):
        pass

    def transfer_update_subscriptions(self):
        pass

    def transfer_flags(self):
        pass

    def transfer_meta_pages(self):
        #here we actually don't have anything in the database yet
        #so we can't do this
        pass

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
            USER[se_u.id] = u
