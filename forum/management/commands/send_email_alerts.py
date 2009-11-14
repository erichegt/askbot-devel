from django.core.management.base import NoArgsCommand
from django.db import connection
from django.db.models import Q, F
from forum.models import *
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
import datetime
import settings

class Command(NoArgsCommand):
    def handle_noargs(self,**options):
        try:
            self.send_email_alerts()
        except Exception, e:
            print e
        finally:
            connection.close()

    def get_updated_questions_for_user(self,user):
        q_sel = []
        q_ask = []
        q_ans = []
        q_all = []
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
                Q_set = Q_set1.exclude(last_activity_at__gt=cutoff_time)
                feed.reported_at = now
                feed.save()#may not actually report anything, depending on filters below
                if feed.feed_type == 'q_sel':
                    q_sel = Q_set.filter(followed_by=user)
                    q_sel.cutoff_time = cutoff_time
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
        q_tbl = {} 
        def extend_question_list(src, dst):
            if isinstance(src,list):
                return
            cutoff_time = src.cutoff_time
            for q in src:
                if q in dst:
                    if cutoff_time < dst[q]:
                        dst[q] = cutoff_time
                else:
                    dst[q] = cutoff_time

        extend_question_list(q_sel, q_tbl)
        extend_question_list(q_ask, q_tbl)
        extend_question_list(q_ans, q_tbl)
        extend_question_list(q_all, q_tbl)

        ctype = ContentType.objects.get_for_model(Question)
        out = {}
        for q, cutoff_time in q_tbl.items():
            #todo use Activity, but first start keeping more Activity records
            #act = Activity.objects.filter(content_type=ctype, object_id=q.id)
            #get info on question edits, answer edits, comments
            out[q] = {}
            q_rev = QuestionRevision.objects.filter(question=q,revised_at__lt=cutoff_time)
            q_rev = q_rev.exclude(author=user)
            out[q]['q_rev'] = len(q_rev)
            if len(q_rev) > 0 and q.added_at == q_rev[0].revised_at:
                out[q]['q_rev'] = 0
                out[q]['new_q'] = True
            else:
                out[q]['new_q'] = False
                
            new_ans = Answer.objects.filter(question=q,added_at__lt=cutoff_time)
            new_ans = new_ans.exclude(author=user)
            out[q]['new_ans'] = len(new_ans)
            ans_rev = AnswerRevision.objects.filter(answer__question=q,revised_at__lt=cutoff_time)
            ans_rev = ans_rev.exclude(author=user)
            out[q]['ans_rev'] = len(ans_rev)
        return out 

    def __act_count(self,string,number,output):
        if number > 0:
            output.append(_(string) % {'num':number})

    def send_email_alerts(self):

        for user in User.objects.all():
            q_list = self.get_updated_questions_for_user(user)
            num_q = len(q_list)
            if num_q > 0:
                url_prefix = settings.APP_URL
                subject = _('email update message subject')
                text = ungettext('%(name)s, this is an update message header for a question', 
                            '%(name)s, this is an update message header for %(num)d questions',num_q) \
                                % {'num':num_q, 'name':user.username}

                text += '<ul>'
                for q, act in q_list.items():
                    act_list = []
                    if act['new_q']:
                        act_list.append(_('new question'))
                    self.__act_count('%(num)d rev', act['q_rev'],act_list)
                    self.__act_count('%(num)d ans', act['new_ans'],act_list)
                    self.__act_count('%(num)d ans rev',act['ans_rev'],act_list)
                    act_token = ', '.join(act_list)
                    text += '<li><a href="%s?sort=latest">%s</a> <font color="#777777">(%s)</font></li>' \
                                % (url_prefix + q.get_absolute_url(), q.title, act_token)
                text += '</ul>'
                link = url_prefix + user.get_profile_url() + '?sort=email_subscriptions'
                text += _('go to %(link)s to change frequency of email updates or %(email)s administrator') \
                                % {'link':link, 'email':settings.ADMINS[0][1]}
                msg = EmailMessage(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email])
                msg.content_subtype = 'html'
                msg.send()
