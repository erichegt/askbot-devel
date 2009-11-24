from django.core.management.base import NoArgsCommand
from django.db import connection
from django.db.models import Q, F
from forum.models import *
from forum import const 
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
import datetime
import settings
import logging
from utils.odict import OrderedDict

class Command(NoArgsCommand):
    def handle_noargs(self,**options):
        try:
            self.send_email_alerts()
        except Exception, e:
            print e
        finally:
            connection.close()

    def get_updated_questions_for_user(self,user):
        q_sel = None 
        q_ask = None 
        q_ans = None 
        q_all = None 
        now = datetime.datetime.now()
        Q_set1 = Question.objects.exclude(
                                        last_activity_by=user,
                                  ).exclude(
                                        last_activity_at__lt=user.date_joined
                                  ).filter(
                                        Q(viewed__who=user,viewed__when__lt=F('last_activity_at')) | \
                                        ~Q(viewed__who=user)
                                  ).exclude(
                                        deleted=True
                                  ).exclude(
                                        closed=True
                                  )
        user_feeds = EmailFeedSetting.objects.filter(subscriber=user).exclude(frequency='n')
        for feed in user_feeds:
            cutoff_time = now - EmailFeedSetting.DELTA_TABLE[feed.frequency]
            if feed.reported_at == None or feed.reported_at <= cutoff_time:
                Q_set = Q_set1.exclude(last_activity_at__gt=cutoff_time)#report these excluded later
                feed.reported_at = now
                feed.save()#may not actually report anything, depending on filters below
                if feed.feed_type == 'q_sel':
                    q_sel = Q_set.filter(followed_by=user)
                    q_sel.cutoff_time = cutoff_time #store cutoff time per query set
                elif feed.feed_type == 'q_ask':
                    q_ask = Q_set.filter(author=user)
                    q_ask.cutoff_time = cutoff_time
                elif feed.feed_type == 'q_ans':
                    q_ans = Q_set.filter(answers__author=user)
                    q_ans.cutoff_time = cutoff_time
                elif feed.feed_type == 'q_all':
                    q_all = Q_set
                    q_all.cutoff_time = cutoff_time
        #build list in this order
        q_list = OrderedDict()
        def extend_question_list(src, dst):
            """src is a query set with questions
               or an empty list
                dst - is an ordered dictionary
            """
            if src is None:
                return #will not do anything if subscription of this type is not used
            cutoff_time = src.cutoff_time
            for q in src:
                if q in dst:
                    if cutoff_time < dst[q]['cutoff_time']:
                        dst[q]['cutoff_time'] = cutoff_time
                else:
                    #initialise a questions metadata dictionary to use for email reporting
                    dst[q] = {'cutoff_time':cutoff_time}

        extend_question_list(q_sel, q_list)
        extend_question_list(q_ask, q_list)
        extend_question_list(q_ans, q_list)
        extend_question_list(q_all, q_list)

        ctype = ContentType.objects.get_for_model(Question)
        EMAIL_UPDATE_ACTIVITY = const.TYPE_ACTIVITY_QUESTION_EMAIL_UPDATE_SENT
        for q, meta_data in q_list.items():
            #todo use Activity, but first start keeping more Activity records
            #act = Activity.objects.filter(content_type=ctype, object_id=q.id)
            #because currently activity is not fully recorded to through
            #revision records to see what kind modifications were done on
            #the questions and answers
            try:
                update_info = Activity.objects.get(content_type=ctype, 
                                                    object_id=q.id,
                                                    activity_type=EMAIL_UPDATE_ACTIVITY)
                emailed_at = update_info.active_at
            except Activity.DoesNotExist:
                update_info = Activity(user=user, content_object=q, activity_type=EMAIL_UPDATE_ACTIVITY)
                emailed_at = datetime.datetime(1970,1,1)#long time ago
            except Activity.MultipleObjectsReturned:
                raise Exception('server error - multiple question email activities found per user-question pair')

            q_rev = QuestionRevision.objects.filter(question=q,\
                                                    revised_at__lt=cutoff_time,\
                                                    revised_at__gt=emailed_at)
            q_rev = q_rev.exclude(author=user)
            meta_data['q_rev'] = len(q_rev)
            if len(q_rev) > 0 and q.added_at == q_rev[0].revised_at:
                meta_data['q_rev'] = 0
                meta_data['new_q'] = True
            else:
                meta_data['new_q'] = False
                
            new_ans = Answer.objects.filter(question=q,\
                                            added_at__lt=cutoff_time,\
                                            added_at__gt=emailed_at)
            new_ans = new_ans.exclude(author=user)
            meta_data['new_ans'] = len(new_ans)
            ans_rev = AnswerRevision.objects.filter(answer__question=q,\
                                            revised_at__lt=cutoff_time,\
                                            revised_at__gt=emailed_at)
            ans_rev = ans_rev.exclude(author=user)
            meta_data['ans_rev'] = len(ans_rev)
            if len(q_rev) == 0 and len(new_ans) == 0 and len(ans_rev) == 0:
                meta_data['nothing_new'] = True
            else:
                meta_data['nothing_new'] = False
                update_info.active_at = now
                update_info.save() #save question email update activity 
        return q_list 

    def __action_count(self,string,number,output):
        if number > 0:
            output.append(_(string) % {'num':number})

    def send_email_alerts(self):

        #todo: move this to template
        for user in User.objects.all():
            q_list = self.get_updated_questions_for_user(user)
            num_q = 0
            num_moot = 0
            for meta_data in q_list.values():
                if meta_data['nothing_new'] == False:
                    num_q += 1
                else:
                    num_moot += 1
            if num_q > 0:
                url_prefix = settings.APP_URL
                subject = _('email update message subject')
                text = ungettext('%(name)s, this is an update message header for a question', 
                            '%(name)s, this is an update message header for %(num)d questions',num_q) \
                                % {'num':num_q, 'name':user.username}

                text += '<ul>'
                for q, meta_data in q_list.items():
                    act_list = []
                    if meta_data['nothing_new']:
                        continue
                    else:
                        if meta_data['new_q']:
                            act_list.append(_('new question'))
                        self.__action_count('%(num)d rev', meta_data['q_rev'],act_list)
                        self.__action_count('%(num)d ans', meta_data['new_ans'],act_list)
                        self.__action_count('%(num)d ans rev',meta_data['ans_rev'],act_list)
                        act_token = ', '.join(act_list)
                        text += '<li><a href="%s?sort=latest">%s</a> <font color="#777777">(%s)</font></li>' \
                                    % (url_prefix + q.get_absolute_url(), q.title, act_token)
                text += '</ul>'
                if num_moot > 0:
                    text += '<p></p>'
                    text += ungettext('There is also one question which was recently '\
                                +'updated but you might not have seen its latest version.',
                            'There are also %(num)d more questions which were recently updated '\
                            +'but you might not have seen their latest version.',num_moot) \
                                % {'num':num_moot,}
                    text += _('Perhaps you could look up previously sent forum reminders in your mailbox.')
                    text += '</p>'

                link = url_prefix + user.get_profile_url() + '?sort=email_subscriptions'
                text += _('go to %(link)s to change frequency of email updates or %(email)s administrator') \
                                % {'link':link, 'email':settings.ADMINS[0][1]}
                msg = EmailMessage(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email])
                msg.content_subtype = 'html'
                msg.send()
