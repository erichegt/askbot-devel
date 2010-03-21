from django.core.management.base import NoArgsCommand
from django.db import connection
from django.db.models import Q, F
from forum.models import *
from forum import const 
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
import datetime
from django.conf import settings
import logging
from forum.utils.odict import OrderedDict
from django.contrib.contenttypes.models import ContentType
from forum import const

def extend_question_list(src, dst, limit=False):
    """src is a query set with questions
       or None
       dst - is an ordered dictionary
    """
    if limit and len(dst.keys()) >= const.MAX_ALERTS_PER_EMAIL:
        return
    if src is None:#is not QuerySet
        return #will not do anything if subscription of this type is not used
    cutoff_time = src.cutoff_time
    for q in src:
        if q in dst:
            #the latest cutoff time wins for a given question
            #if the question falls into several subscription groups
            if cutoff_time > dst[q]['cutoff_time']:
                dst[q]['cutoff_time'] = cutoff_time
        else:
            #initialise a questions metadata dictionary to use for email reporting
            dst[q] = {'cutoff_time':cutoff_time}

class Command(NoArgsCommand):
    def handle_noargs(self,**options):
        try:
            try:
                self.send_email_alerts()
            except Exception, e:
                print e
        finally:
            connection.close()

    def get_updated_questions_for_user(self,user):

        #these are placeholders for separate query sets per question group
        #there are four groups - one for each EmailFeedSetting.feed_type
        #and each group has subtypes A and B
        #that's because of the strange thing commented below
        #see note on Q and F objects marked with todo tag
        q_sel_A = None
        q_sel_B = None

        q_ask_A = None
        q_ask_B = None

        q_ans_A = None
        q_ans_B = None

        q_all_A = None
        q_all_B = None

        now = datetime.datetime.now()
        #Q_set1 - base questionquery set for this user
        Q_set1 = Question.objects.exclude(
                                last_activity_by=user
                            ).exclude(
                                last_activity_at__lt=user.date_joined#exclude old stuff
                            ).exclude(
                                deleted=True
                            ).exclude(
                                closed=True
                            ).order_by('-last_activity_at')
        #todo: for some reason filter on did not work as expected ~Q(viewed__who=user) | 
        #      Q(viewed__who=user,viewed__when__lt=F('last_activity_at'))
        #returns way more questions than you might think it should
        #so because of that I've created separate query sets Q_set2 and Q_set3
        #plus two separate queries run faster!

        #questions that are not seen by the user
        Q_set2 = Q_set1.filter(~Q(viewed__who=user))
        #questions seen before the last modification
        Q_set3 = Q_set1.filter(Q(viewed__who=user,viewed__when__lt=F('last_activity_at')))

        #todo may shortcirquit here is len(user_feeds) == 0
        user_feeds = EmailFeedSetting.objects.filter(subscriber=user).exclude(frequency='n')
        if len(user_feeds) == 0:
            return {};#short cirquit
        for feed in user_feeds:
            #each group of updates has it's own cutoff time
            #to be saved as a new parameter for each query set
            #won't send email for a given question if it has been done
            #after the cutoff_time
            cutoff_time = now - EmailFeedSetting.DELTA_TABLE[feed.frequency]
            if feed.reported_at == None or feed.reported_at <= cutoff_time:
                Q_set_A = Q_set2#.exclude(last_activity_at__gt=cutoff_time)#report these excluded later
                Q_set_B = Q_set3#.exclude(last_activity_at__gt=cutoff_time)
                feed.reported_at = now
                feed.save()#may not actually report anything, depending on filters below
                if feed.feed_type == 'q_sel':
                    q_sel_A = Q_set_A.filter(followed_by=user)
                    q_sel_A.cutoff_time = cutoff_time #store cutoff time per query set
                    q_sel_B = Q_set_B.filter(followed_by=user)
                    q_sel_B.cutoff_time = cutoff_time #store cutoff time per query set
                elif feed.feed_type == 'q_ask':
                    q_ask_A = Q_set_A.filter(author=user)
                    q_ask_A.cutoff_time = cutoff_time
                    q_ask_B = Q_set_B.filter(author=user)
                    q_ask_B.cutoff_time = cutoff_time
                elif feed.feed_type == 'q_ans':
                    q_ans_A = Q_set_A.filter(answers__author=user)[:const.MAX_ALERTS_PER_EMAIL]
                    q_ans_A.cutoff_time = cutoff_time
                    q_ans_B = Q_set_B.filter(answers__author=user)[:const.MAX_ALERTS_PER_EMAIL]
                    q_ans_B.cutoff_time = cutoff_time
                elif feed.feed_type == 'q_all':
                    if user.tag_filter_setting == 'ignored':
                        ignored_tags = Tag.objects.filter(user_selections__reason='bad', \
                                                            user_selections__user=user)
                        q_all_A = Q_set_A.exclude( tags__in=ignored_tags )[:const.MAX_ALERTS_PER_EMAIL]
                        q_all_B = Q_set_B.exclude( tags__in=ignored_tags )[:const.MAX_ALERTS_PER_EMAIL]
                    else:
                        selected_tags = Tag.objects.filter(user_selections__reason='good', \
                                                            user_selections__user=user)
                        q_all_A = Q_set_A.filter( tags__in=selected_tags )
                        q_all_B = Q_set_B.filter( tags__in=selected_tags )
                    q_all_A.cutoff_time = cutoff_time
                    q_all_B.cutoff_time = cutoff_time
        #build list in this order
        q_list = OrderedDict()

        extend_question_list(q_sel_A, q_list)
        extend_question_list(q_sel_B, q_list)

        if user.tag_filter_setting == 'interesting':
            extend_question_list(q_all_A, q_list)
            extend_question_list(q_all_B, q_list)

        extend_question_list(q_ask_A, q_list, limit=True)
        extend_question_list(q_ask_B, q_list, limit=True)

        extend_question_list(q_ans_A, q_list, limit=True)
        extend_question_list(q_ans_B, q_list, limit=True)

        if user.tag_filter_setting == 'ignored':
            extend_question_list(q_all_A, q_list, limit=True)
            extend_question_list(q_all_B, q_list, limit=True)

        ctype = ContentType.objects.get_for_model(Question)
        EMAIL_UPDATE_ACTIVITY = const.TYPE_ACTIVITY_QUESTION_EMAIL_UPDATE_SENT
        for q, meta_data in q_list.items():
            #this loop edits meta_data for each question
            #so that user will receive counts on new edits new answers, etc
            #maybe not so important actually??

            #keeps email activity per question per user
            try:
                update_info = Activity.objects.get(
                                                    user=user,
                                                    content_type=ctype,
                                                    object_id=q.id,
                                                    activity_type=EMAIL_UPDATE_ACTIVITY
                                                    )
                emailed_at = update_info.active_at
            except Activity.DoesNotExist:
                update_info = Activity(user=user, content_object=q, activity_type=EMAIL_UPDATE_ACTIVITY)
                emailed_at = datetime.datetime(1970,1,1)#long time ago
            except Activity.MultipleObjectsReturned:
                raise Exception('server error - multiple question email activities found per user-question pair')

            cutoff_time = meta_data['cutoff_time']#cutoff time for the question

            #wait some more time before emailing about this question
            if emailed_at > cutoff_time:
                #here we are maybe losing opportunity to record the finding
                #of yet unseen version of a question
                meta_data['skip'] = True
                continue

            #collect info on all sorts of news that happened after
            #the most recent emailing to the user about this question
            q_rev = QuestionRevision.objects.filter(question=q,\
                                                    revised_at__gt=emailed_at)
            q_rev = q_rev.exclude(author=user)

            #now update all sorts of metadata per question
            meta_data['q_rev'] = len(q_rev)
            if len(q_rev) > 0 and q.added_at == q_rev[0].revised_at:
                meta_data['q_rev'] = 0
                meta_data['new_q'] = True
            else:
                meta_data['new_q'] = False
                
            new_ans = Answer.objects.filter(question=q,\
                                            added_at__gt=emailed_at)
            new_ans = new_ans.exclude(author=user)
            meta_data['new_ans'] = len(new_ans)
            ans_rev = AnswerRevision.objects.filter(answer__question=q,\
                                            revised_at__gt=emailed_at)
            ans_rev = ans_rev.exclude(author=user)
            meta_data['ans_rev'] = len(ans_rev)

            if 0 in (len(q_rev), len(new_ans), len(ans_rev)):
                meta_data['skip'] = True
            else:
                meta_data['skip'] = False
                update_info.active_at = now
                update_info.save() #save question email update activity 
        #q_list is actually a ordered dictionary
        #print 'user %s gets %d' % (user.username, len(q_list.keys()))
        #todo: sort question list by update time
        return q_list 

    def __action_count(self,string,number,output):
        if number > 0:
            output.append(_(string) % {'num':number})

    def send_email_alerts(self):
        #does not change the database, only sends the email
        #todo: move this to template
        for user in User.objects.all():
            #todo: q_list is a dictionary, not a list
            q_list = self.get_updated_questions_for_user(user)
            if len(q_list.keys()) == 0:
                continue
            num_q = 0
            num_moot = 0
            for meta_data in q_list.values():
                if meta_data['skip']:
                    num_moot = True
                else:
                    num_q += 1
            if num_q > 0:
                url_prefix = settings.APP_URL
                subject = _('email update message subject')
                print 'have %d updated questions for %s' % (num_q, user.username)
                text = ungettext('%(name)s, this is an update message header for a question', 
                            '%(name)s, this is an update message header for %(num)d questions',num_q) \
                                % {'num':num_q, 'name':user.username}

                text += '<ul>'
                items_added = 0
                items_unreported = 0
                for q, meta_data in q_list.items():
                    act_list = []
                    if meta_data['skip']:
                        continue
                    if items_added >= const.MAX_ALERTS_PER_EMAIL:
                        items_unreported = num_q - items_added #may be inaccurate actually, but it's ok
                        
                    else:
                        items_added += 1
                        if meta_data['new_q']:
                            act_list.append(_('new question'))
                        self.__action_count('%(num)d rev', meta_data['q_rev'],act_list)
                        self.__action_count('%(num)d ans', meta_data['new_ans'],act_list)
                        self.__action_count('%(num)d ans rev',meta_data['ans_rev'],act_list)
                        act_token = ', '.join(act_list)
                        text += '<li><a href="%s?sort=latest">%s</a> <font color="#777777">(%s)</font></li>' \
                                    % (url_prefix + q.get_absolute_url(), q.title, act_token)
                text += '</ul>'
                text += '<p></p>'
                #if len(q_list.keys()) >= const.MAX_ALERTS_PER_EMAIL:
                #    text += _('There may be more questions updated since '
                #                'you have logged in last time as this list is '
                #                'abridged for your convinience. Please visit '
                #                'the forum and see what\'s new!<br>'
                #              )

                text += _(
                            'Please visit the forum and see what\'s new! '
                            'Could you spread the word about it - '
                            'can somebody you know help answering those questions or '
                            'benefit from posting one?'
                        )

                feeds = EmailFeedSetting.objects.filter(
                                                        subscriber=user,
                                                    )
                feed_freq = [feed.frequency for feed in feeds]
                text += '<p></p>'
                if 'd' in feed_freq:
                    text += _('Your most frequent subscription setting is \'daily\' '
                               'on selected questions. If you are receiving more than one '
                               'email per day'
                               'please tell about this issue to the forum administrator.'
                               )
                elif 'w' in feed_freq:
                    text += _('Your most frequent subscription setting is \'weekly\' '
                               'if you are receiving this email more than once a week '
                               'please report this issue to the forum administrator.'
                               )
                text += ' '
                text += _(
                            'There is a chance that you may be receiving links seen '
                            'before - due to a technicality that will eventually go away. '
                        )
                #    text += '</p>'
                #if num_moot > 0:
                #    text += '<p></p>'
                #    text += ungettext('There is also one question which was recently '\
                #                +'updated but you might not have seen its latest version.',
                #            'There are also %(num)d more questions which were recently updated '\
                #            +'but you might not have seen their latest version.',num_moot) \
                #                % {'num':num_moot,}
                #    text += _('Perhaps you could look up previously sent forum reminders in your mailbox.')
                #    text += '</p>'

                link = url_prefix + user.get_profile_url() + '?sort=email_subscriptions'
                text += _('go to %(link)s to change frequency of email updates or %(email)s administrator') \
                                % {'link':link, 'email':settings.ADMINS[0][1]}
                msg = EmailMessage(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email])
                msg.content_subtype = 'html'
                msg.send()
                #uncomment lines below to get copies of emails sent to others
                #todo: maybe some debug setting would be appropriate here
                #msg2 = EmailMessage(subject, text, settings.DEFAULT_FROM_EMAIL, ['your@email.com'])
                #msg2.content_subtype = 'html'
                #msg2.send()
