"""
Authorisation related functions.

The actions a User is authorised to perform are dependent on their reputation
and superuser status.
"""
import datetime
from django.utils.translation import ugettext as _
from django.db import transaction
from models import Repute
from models import Question
from models import Answer
from models import mark_offensive, delete_post_or_answer
from const import TYPE_REPUTATION
import logging

from livesettings import ConfigurationGroup, IntegerValue, config_register
MINIMUM_REPUTATION_SETTINGS = ConfigurationGroup(
                                'MIN_REP', 
                                _('Minimum reputation settings'), 
                                ordering=0)

MIN_REP_DATA = (
    #(key, min_rep, description),
    ('VOTE_UP', 15, _('Vote')),
    ('FLAG_OFFENSIVE', 15, _('Flag offensive')),
    #('POST_IMAGES', 15, _('Upload images')),#todo: looks like unused
    ('LEAVE_COMMENTS', 50, _('Leave comments')),
    ('UPLOAD_FILES', 60, _('Upload files')),
    ('VOTE_DOWN', 100, _('Downvote')),
    ('CLOSE_OWN_QUESTIONS', 250, _('Close own questions')),
    ('RETAG_OTHER_QUESTIONS', 500, _('Retag questions posted by other people')),
    ('REOPEN_OWN_QUESTIONS', 500, _('Reopen own questions')),
    ('EDIT_COMMUNITY_WIKI_POSTS', 750, _('Edit community wiki posts')),
    ('EDIT_OTHER_POSTS', 2000, _('Edit posts authored by other people')),
    ('DELETE_COMMENTS', 2000, _('Delete comments')),
    ('VIEW_OFFENSIVE_FLAGS', 2000, _('View offensive flags')),
    ('DISABLE_URL_NOFOLLOW', 2000, _('Disable url nofollow')),
    ('CLOSE_OTHER_QUESTIONS', 3000, _('Close questions asked by others')),
    ('LOCK_POSTS', 4000, _('Lock posts')),
)

#rolled into eval block to save on typing an debugging
python_format_string = '%(VAR_NAME)s = config_register(IntegerValue(%(SETTINGS_GROUP_KEY)s,\'%(VAR_NAME)s\', default = %(DEFAULT_VALUE)d,description = u\'%(VAR_DESCRIPTION)s\', ordering=%(ORDERING)d))\n'
i = 0
for item in MIN_REP_DATA:
    name = item[0]
    value = item[1]
    description = item[2]
    python_string = python_format_string \
                % {
                'SETTINGS_GROUP_KEY':'MINIMUM_REPUTATION_SETTINGS',
                'VAR_NAME':name, 
                'DEFAULT_VALUE':value, 
                'VAR_DESCRIPTION':description, 
                'ORDERING':i,
                }
    i += 1
    exec(python_string)

VOTE_RULES_DATA = (
    ('scope_votes_per_user_per_day', 30, _('Maximum votes per day')), # how many votes of one user has everyday
    ('scope_flags_per_user_per_day', 5, _('Maximum flags per day')), # how many times user can flag posts everyday
    ('scope_warn_votes_left', 5, _('How early to start warning about the vote per day limit')), # start when to warn user how many votes left
    ('scope_deny_unvote_days', 1, _('Days to allow canceling votes')), # if 1 days passed, user can't cancel votes.
    ('scope_flags_invisible_main_page', 3, _('Number of flags to hide post')), # post doesn't show on main page if has more than 3 offensive flags
    ('scope_flags_delete_post', 5, _('Number of flags to delete post')),# post will be deleted if it has more than 5 offensive flags
)

VOTE_RULE_SETTINGS = ConfigurationGroup(
                                'VOTE_RULES', 
                                _('Vote and flag rules'), 
                                ordering=0)

i = 0
for item in VOTE_RULES_DATA:
    name = item[0]
    value = item[1]
    description = item[2]
    python_string = python_format_string \
                % {
                'SETTINGS_GROUP_KEY':'VOTE_RULE_SETTINGS',
                'VAR_NAME':name, 
                'DEFAULT_VALUE':value, 
                'VAR_DESCRIPTION':description, 
                'ORDERING':i,
                }
    i += 1
    exec(python_string)

VOTE_RULES = {
    'scope_votes_per_user_per_day' : scope_votes_per_user_per_day, # how many votes of one user has everyday
    'scope_flags_per_user_per_day' : scope_flags_per_user_per_day,  # how many times user can flag posts everyday
    'scope_warn_votes_left' : scope_warn_votes_left, # start when to warn user how many votes left
    'scope_deny_unvote_days' : scope_deny_unvote_days, # if 1 days passed, user can't cancel votes.
    'scope_flags_invisible_main_page' : scope_flags_invisible_main_page, # post doesn't show on main page if has more than 3 offensive flags
    'scope_flags_delete_post' : scope_flags_delete_post, # post will be deleted if it has more than 5 offensive flags
}

REPUTATION_RULES = {
    'initial_score'                       : 1,
    'scope_per_day_by_upvotes'            : 200,
    'gain_by_upvoted'                     : 10,
    'gain_by_answer_accepted'             : 15,
    'gain_by_accepting_answer'            : 2,
    'gain_by_downvote_canceled'           : 2,
    'gain_by_canceling_downvote'          : 1,
    'lose_by_canceling_accepted_answer'   : -2,
    'lose_by_accepted_answer_cancled'     : -15,
    'lose_by_downvoted'                   : -2,
    'lose_by_flagged'                     : -2,
    'lose_by_downvoting'                  : -1,
    'lose_by_flagged_lastrevision_3_times': -30,
    'lose_by_flagged_lastrevision_5_times': -100,
    'lose_by_upvote_canceled'             : -10,
}

def can_moderate_users(user):
    return user.is_superuser

def can_vote_up(user):
    """Determines if a User can vote Questions and Answers up."""
    return user.is_authenticated() and (
        user.reputation >= VOTE_UP.value or
        user.is_superuser)

def can_flag_offensive(user):
    """Determines if a User can flag Questions and Answers as offensive."""
    return user.is_authenticated() and (
        user.reputation >= FLAG_OFFENSIVE.value or
        user.is_superuser)

def can_add_comments(user,subject):
    """Determines if a User can add comments to Questions and Answers."""
    if user.is_authenticated():
        if user.id == subject.author.id:
            return True
        if user.reputation >= LEAVE_COMMENTS.value:
            return True
        if user.is_superuser:
            return True
        if isinstance(subject,Answer) and subject.question.author.id == user.id:
            return True
    return False

def can_vote_down(user):
    """Determines if a User can vote Questions and Answers down."""
    return user.is_authenticated() and (
        user.reputation >= VOTE_DOWN.value or
        user.is_superuser)

def can_retag_questions(user):
    """Determines if a User can retag Questions."""
    return user.is_authenticated() and (
        RETAG_OTHER_QUESTIONS.value <= user.reputation < EDIT_OTHER_POSTS.value or
        user.is_superuser)

def can_edit_post(user, post):
    """Determines if a User can edit the given Question or Answer."""
    return user.is_authenticated() and (
        user.id == post.author_id or
        (post.wiki and user.reputation >= EDIT_COMMUNITY_WIKI_POSTS.value) or
        user.reputation >= EDIT_OTHER_POSTS.value or
        user.is_superuser)

def can_delete_comment(user, comment):
    """Determines if a User can delete the given Comment."""
    return user.is_authenticated() and (
        user.id == comment.user_id or
        user.reputation >= DELETE_COMMENTS.value or
        user.is_superuser)

def can_view_offensive_flags(user):
    """Determines if a User can view offensive flag counts."""
    return user.is_authenticated() and (
        user.reputation >= VIEW_OFFENSIVE_FLAGS.value or
        user.is_superuser)

def can_close_question(user, question):
    """Determines if a User can close the given Question."""
    return user.is_authenticated() and (
        (user.id == question.author_id and
         user.reputation >= CLOSE_OWN_QUESTIONS.value) or
        user.reputation >= CLOSE_OTHER_QUESTIONS.value or
        user.is_superuser)

def can_lock_posts(user):
    """Determines if a User can lock Questions or Answers."""
    return user.is_authenticated() and (
        user.reputation >= LOCK_POSTS.value or
        user.is_superuser)

def can_follow_url(user):
    """Determines if the URL link can be followed by Google search engine."""
    return user.reputation >= DISABLE_URL_NOFOLLOW.value

def can_accept_answer(user, question, answer):
    return (user.is_authenticated() and
        question.author != answer.author and
        question.author == user) or user.is_superuser

# now only support to reopen own question except superuser
def can_reopen_question(user, question):
    return (user.is_authenticated() and
        user.id == question.author_id and
        user.reputation >= REOPEN_OWN_QUESTIONS.value) or user.is_superuser

def can_delete_post(user, post):
    if user.is_superuser:
        return True
    elif user.is_authenticated() and user == post.author:
        if isinstance(post,Answer):
            return True
        elif isinstance(post,Question):
            answers = post.answers.all()
            for answer in answers:
                if user != answer.author and answer.deleted == False:
                    return False
            return True
        else:
            return False
    else:
        return False

def can_view_deleted_post(user, post):
    return user.is_superuser

# user preferences view permissions
def is_user_self(request_user, target_user):
    return (request_user.is_authenticated() and request_user == target_user)
    
def can_view_user_votes(request_user, target_user):
    return (request_user.is_authenticated() and request_user == target_user)

def can_view_user_preferences(request_user, target_user):
    return (request_user.is_authenticated() and request_user == target_user)

def can_view_user_edit(request_user, target_user):
    return (request_user.is_authenticated() and request_user == target_user)

def can_upload_files(request_user):
    return (request_user.is_authenticated() and request_user.reputation >= UPLOAD_FILES.value) or \
           request_user.is_superuser

###########################################
## actions and reputation changes event
###########################################
def calculate_reputation(origin, offset):
    result = int(origin) + int(offset)
    if (result > 0):
        return result
    else:
        return 1

@transaction.commit_on_success
def onFlaggedItem(item, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()

    item.save()
    post.offensive_flag_count = post.offensive_flag_count + 1
    post.save()

    post.author.reputation = calculate_reputation(post.author.reputation,
                           int(REPUTATION_RULES['lose_by_flagged'].value))
    post.author.save()

    question = post
    if isinstance(post, Answer):
        question = post.question

    reputation = Repute(user=post.author,
               negative=int(REPUTATION_RULES['lose_by_flagged'].value),
               question=question, reputed_at=timestamp,
               reputation_type=-4,
               reputation=post.author.reputation)
    reputation.save()

    #todo: These should be updated to work on same revisions.
    if post.offensive_flag_count ==  VOTE_RULES['scope_flags_invisible_main_page'].value :
        post.author.reputation = calculate_reputation(post.author.reputation,
                               int(REPUTATION_RULES['lose_by_flagged_lastrevision_3_times'].value))
        post.author.save()

        reputation = Repute(user=post.author,
                   negative=int(REPUTATION_RULES['lose_by_flagged_lastrevision_3_times'].value),
                   question=question,
                   reputed_at=timestamp,
                   reputation_type=-6,
                   reputation=post.author.reputation)
        reputation.save()

    elif post.offensive_flag_count == VOTE_RULES['scope_flags_delete_post'].value :
        post.author.reputation = calculate_reputation(post.author.reputation,
                               int(REPUTATION_RULES['lose_by_flagged_lastrevision_5_times'].value))
        post.author.save()

        reputation = Repute(user=post.author,
                   negative=int(REPUTATION_RULES['lose_by_flagged_lastrevision_5_times'].value),
                   question=question,
                   reputed_at=timestamp,
                   reputation_type=-7,
                   reputation=post.author.reputation)
        reputation.save()

        post.deleted = True
        #post.deleted_at = timestamp
        #post.deleted_by = Admin
        post.save()
        mark_offensive.send(
            sender=post.__class__, 
            instance=post, 
            mark_by=user
        )

@transaction.commit_on_success
def onAnswerAccept(answer, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()

    answer.accepted = True
    answer.accepted_at = timestamp
    answer.question.answer_accepted = True
    answer.save()
    answer.question.save()

    answer.author.reputation = calculate_reputation(answer.author.reputation,
                             int(REPUTATION_RULES['gain_by_answer_accepted'].value))
    answer.author.save()
    reputation = Repute(user=answer.author,
               positive=int(REPUTATION_RULES['gain_by_answer_accepted'].value),
               question=answer.question,
               reputed_at=timestamp,
               reputation_type=2,
               reputation=answer.author.reputation)
    reputation.save()

    user.reputation = calculate_reputation(user.reputation,
                    int(REPUTATION_RULES['gain_by_accepting_answer'].value))
    user.save()
    reputation = Repute(user=user,
               positive=int(REPUTATION_RULES['gain_by_accepting_answer'].value),
               question=answer.question,
               reputed_at=timestamp,
               reputation_type=3,
               reputation=user.reputation)
    reputation.save()

@transaction.commit_on_success
def onAnswerAcceptCanceled(answer, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    answer.accepted = False
    answer.accepted_at = None
    answer.question.answer_accepted = False
    answer.save()
    answer.question.save()

    answer.author.reputation = calculate_reputation(answer.author.reputation,
                             int(REPUTATION_RULES['lose_by_accepted_answer_cancled'].value))
    answer.author.save()
    reputation = Repute(user=answer.author,
               negative=int(REPUTATION_RULES['lose_by_accepted_answer_cancled'].value),
               question=answer.question,
               reputed_at=timestamp,
               reputation_type=-2,
               reputation=answer.author.reputation)
    reputation.save()

    user.reputation = calculate_reputation(user.reputation,
                    int(REPUTATION_RULES['lose_by_canceling_accepted_answer'].value))
    user.save()
    reputation = Repute(user=user,
               negative=int(REPUTATION_RULES['lose_by_canceling_accepted_answer'].value),
               question=answer.question,
               reputed_at=timestamp,
               reputation_type=-1,
               reputation=user.reputation)
    reputation.save()

@transaction.commit_on_success
def onUpVoted(vote, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    vote.save()

    post.vote_up_count = int(post.vote_up_count) + 1
    post.score = int(post.score) + 1
    post.save()

    if not post.wiki:
        author = post.author
        todays_rep_gain = Repute.objects.get_reputation_by_upvoted_today(author)
        if todays_rep_gain <  int(REPUTATION_RULES['scope_per_day_by_upvotes'].value):
            author.reputation = calculate_reputation(author.reputation,
                              int(REPUTATION_RULES['gain_by_upvoted'].value))
            author.save()

            question = post
            if isinstance(post, Answer):
                question = post.question

            reputation = Repute(user=author,
                       positive=int(REPUTATION_RULES['gain_by_upvoted'].value),
                       question=question,
                       reputed_at=timestamp,
                       reputation_type=1,
                       reputation=author.reputation)
            reputation.save()

@transaction.commit_on_success
def onUpVotedCanceled(vote, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    vote.delete()

    post.vote_up_count = int(post.vote_up_count) - 1
    if post.vote_up_count < 0:
        post.vote_up_count  = 0
    post.score = int(post.score) - 1
    post.save()

    if not post.wiki:
        author = post.author
        author.reputation = calculate_reputation(author.reputation,
                          int(REPUTATION_RULES['lose_by_upvote_canceled'].value))
        author.save()

        question = post
        if isinstance(post, Answer):
            question = post.question

        reputation = Repute(user=author,
                   negative=int(REPUTATION_RULES['lose_by_upvote_canceled'].value),
                   question=question,
                   reputed_at=timestamp,
                   reputation_type=-8,
                   reputation=author.reputation)
        reputation.save()

@transaction.commit_on_success
def onDownVoted(vote, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    vote.save()

    post.vote_down_count = int(post.vote_down_count) + 1
    post.score = int(post.score) - 1
    post.save()

    if not post.wiki:
        author = post.author
        author.reputation = calculate_reputation(author.reputation,
                          int(REPUTATION_RULES['lose_by_downvoted'].value))
        author.save()

        question = post
        if isinstance(post, Answer):
            question = post.question

        reputation = Repute(user=author,
                   negative=int(REPUTATION_RULES['lose_by_downvoted'].value),
                   question=question,
                   reputed_at=timestamp,
                   reputation_type=-3,
                   reputation=author.reputation)
        reputation.save()

        user.reputation = calculate_reputation(user.reputation,
                        int(REPUTATION_RULES['lose_by_downvoting'].value))
        user.save()

        reputation = Repute(user=user,
                   negative=int(REPUTATION_RULES['lose_by_downvoting'].value),
                   question=question,
                   reputed_at=timestamp,
                   reputation_type=-5,
                   reputation=user.reputation)
        reputation.save()

@transaction.commit_on_success
def onDownVotedCanceled(vote, post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    vote.delete()

    post.vote_down_count = int(post.vote_down_count) - 1
    if post.vote_down_count < 0:
        post.vote_down_count  = 0
    post.score = post.score + 1
    post.save()

    if not post.wiki:
        author = post.author
        author.reputation = calculate_reputation(author.reputation,
                          int(REPUTATION_RULES['gain_by_downvote_canceled'].value))
        author.save()

        question = post
        if isinstance(post, Answer):
            question = post.question

        reputation = Repute(user=author,
                   positive=int(REPUTATION_RULES['gain_by_downvote_canceled'].value),
                   question=question,
                   reputed_at=timestamp,
                   reputation_type=4,
                   reputation=author.reputation)
        reputation.save()

        user.reputation = calculate_reputation(user.reputation,
                        int(REPUTATION_RULES['gain_by_canceling_downvote'].value))
        user.save()

        reputation = Repute(user=user,
                   positive=int(REPUTATION_RULES['gain_by_canceling_downvote'].value),
                   question=question,
                   reputed_at=timestamp,
                   reputation_type=5,
                   reputation=user.reputation)
        reputation.save()

#here timestamp is not used, I guess added for consistency
def onDeleteCanceled(post, user, timestamp=None):
    post.deleted = False
    post.deleted_by = None 
    post.deleted_at = None 
    post.save()
    logging.debug('now restoring something')
    if isinstance(post,Answer):
        logging.debug('updated answer count on undelete, have %d' % post.question.answer_count)
        Question.objects.update_answer_count(post.question)
    elif isinstance(post,Question):
        for tag in list(post.tags.all()):
            if tag.used_count == 1 and tag.deleted:
                tag.deleted = False
                tag.deleted_by = None
                tag.deleted_at = None 
                tag.save()

def onDeleted(post, user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now()
    post.deleted = True
    post.deleted_by = user
    post.deleted_at = timestamp
    post.save()

    if isinstance(post, Question):
        for tag in list(post.tags.all()):
            if tag.used_count == 1:
                tag.deleted = True
                tag.deleted_by = user
                tag.deleted_at = timestamp
            else:
                tag.used_count = tag.used_count - 1 
            tag.save()

        answers = post.answers.all()
        if user == post.author:
            if len(answers) > 0:
                msg = _('Your question and all of it\'s answers have been deleted')
            else:
                msg = _('Your question has been deleted')
        else:
            if len(answers) > 0:
                msg = _('The question and all of it\'s answers have been deleted')
            else:
                msg = _('The question has been deleted')
        user.message_set.create(message=msg)
        logging.debug('posted a message %s' % msg)
        for answer in answers:
            onDeleted(answer, user)
    elif isinstance(post, Answer):
        Question.objects.update_answer_count(post.question)
        logging.debug('updated answer count to %d' % post.question.answer_count)
    delete_post_or_answer.send(
        sender=post.__class__,
        instance=post,
        delete_by=user
    )
