from django.test import TestCase
from django.core import exceptions
from askbot.tests import utils
from askbot.conf import settings as askbot_settings
from askbot import models

class PermissionAssertionTestCase(TestCase):
    """base TestCase class for permission
    assertion tests

    subclass may redefine method extraSetUp
    """

    def setUp(self):
        self.user = utils.create_user(
                            username = 'test',
                            email = 'test@test.com'
                        )
        self.extraSetUp()

    def extraSetUp(self):
        pass

    def create_other_user(self):
        return utils.create_user(
                        username = 'other',
                        email = 'other@test.com'
                    )

    def post_question(self, author = None):
        if author is None:
            author = self.user
        return author.post_question(
                            title = 'test question title',
                            body_text = 'test question body',
                            tags = 'test'
                        )

    def post_answer(self, question = None, author = None):
        if author is None:
            author = self.user
        return author.post_answer(
                        question = question,
                        body_text = 'test answer'
                    )


class CommentPermissionAssertionTests(PermissionAssertionTestCase):

    def extraSetUp(self):
        self.min_rep = askbot_settings.MIN_REP_TO_LEAVE_COMMENTS
        self.other_user = self.create_other_user()

    def test_blocked_user_cannot_comment_own_question(self):
        question = self.post_question()

        self.user.set_status('b')
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.post_comment,
                    parent_post = question,
                    body_text = 'test comment'
                )

    def test_blocked_user_cannot_comment_own_answer(self):
        question = self.post_question()
        answer = self.post_answer(question)

        self.user.set_status('b')

        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.post_comment,
                    parent_post = answer,
                    body_text = 'test comment'
                )

    def test_blocked_user_cannot_delete_own_comment(self):
        question = self.post_question()
        comment = self.user.post_comment(
                        parent_post = question,
                        body_text = 'test comment'
                    )
        self.user.set_status('b')
        self.assertRaises(
            exceptions.PermissionDenied,
            self.user.delete_post,
            post = comment
        )

    def test_low_rep_user_cannot_delete_others_comment(self):
        question = self.post_question()
        comment = self.user.post_comment(
                        parent_post = question,
                        body_text = 'test comment'
                    )
        assert(
            self.other_user.reputation < \
            askbot_settings.MIN_REP_TO_DELETE_OTHERS_COMMENTS
        )
        self.assertRaises(
            exceptions.PermissionDenied,
            self.other_user.delete_post,
            post = comment
        )

    def test_high_rep_user_can_delete_comment(self):
        question = self.post_question()
        comment = self.user.post_comment(
                        parent_post = question,
                        body_text = 'test comment'
                    )
        self.other_user.reputation = \
            askbot_settings.MIN_REP_TO_DELETE_OTHERS_COMMENTS

        self.other_user.delete_comment(comment)

    def test_low_rep_user_can_delete_own_comment(self):
        question = self.post_question()
        answer = self.other_user.post_answer(
                        question = question,
                        body_text = 'test answer'
                    )
        comment = self.user.post_comment(
                        parent_post = answer,
                        body_text = 'test comment'
                    )
        assert(
            self.user.reputation < \
            askbot_settings.MIN_REP_TO_DELETE_OTHERS_COMMENTS
        )
        self.user.delete_comment(comment)

    def test_moderator_can_delete_comment(self):
        question = self.post_question()
        comment = self.user.post_comment(
                        parent_post = question,
                        body_text = 'test comment'
                    )
        self.other_user.set_status('m')
        self.other_user.delete_comment(comment)

    def test_admin_can_delete_comment(self):
        question = self.post_question()
        comment = self.user.post_comment(
                        parent_post = question,
                        body_text = 'test comment'
                    )
        self.other_user.is_superuser = True
        self.other_user.delete_comment(comment)

    def test_high_rep_suspended_user_cannot_delete_others_comment(self):
        question = self.post_question()
        comment = self.user.post_comment(
                        parent_post = question,
                        body_text = 'test comment'
                    )
        self.other_user.reputation = \
            askbot_settings.MIN_REP_TO_DELETE_OTHERS_COMMENTS + 1
        self.other_user.set_status('s')
        self.assertRaises(
                exceptions.PermissionDenied,
                self.other_user.delete_post,
                post = comment
            )

    def test_suspended_user_can_delete_own_comment(self):
        question = self.post_question()
        comment = self.user.post_comment(
                        parent_post = question,
                        body_text = 'test comment'
                    )
        self.user.set_status('s')
        self.user.delete_comment(comment)

    def test_low_rep_user_cannot_comment_others(self):
        question = self.post_question(
                            author = self.other_user
                        )
        assert(self.user.reputation < self.min_rep)
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.post_comment,
                    parent_post = question,
                    body_text = 'test comment'
                )

    def test_low_rep_user_can_comment_others_answer_to_own_question(self):
        question = self.post_question()
        assert(self.user.reputation < self.min_rep)
        answer = self.other_user.post_answer(
                        question = question,
                        body_text = 'test answer'
                    )
        comment = self.user.post_comment(
                                    parent_post = answer,
                                    body_text = 'test comment'
                                )
        self.assertTrue(isinstance(comment, models.Comment))

    def test_high_rep_user_can_comment(self):
        question = self.post_question(
                            author = self.other_user
                        )
        self.user.reputation = self.min_rep
        comment = self.user.post_comment(
                            parent_post = question,
                            body_text = 'test comment'
                        )
        self.assertTrue(isinstance(comment, models.Comment))

    def test_suspended_user_cannot_comment_others_question(self):
        question = self.post_question(author = self.other_user)
        self.user.set_status('s')
        self.assertRaises(
                exceptions.PermissionDenied,
                self.user.post_comment,
                parent_post = question,
                body_text = 'test comment'
            )

    def test_suspended_user_can_comment_own_question(self):
        question = self.post_question()
        self.user.set_status('s')
        comment = self.user.post_comment(
                            parent_post = question,
                            body_text = 'test comment'
                        )
        self.assertTrue(isinstance(comment, models.Comment))

    def test_low_rep_admin_can_comment_others_question(self):
        question = self.post_question()
        self.other_user.is_superuser = True
        assert(self.other_user.is_administrator())
        assert(self.other_user.reputation < self.min_rep)
        comment = self.other_user.post_comment(
                            parent_post = question,
                            body_text = 'test comment'
                        )
        self.assertTrue(isinstance(comment, models.Comment))

    def test_low_rep_moderator_can_comment_others_question(self):
        question = self.post_question()
        self.other_user.set_status('m')
        assert(self.other_user.is_moderator())
        assert(self.other_user.reputation < self.min_rep)
        comment = self.other_user.post_comment(
                            parent_post = question,
                            body_text = 'test comment'
                        )
        self.assertTrue(isinstance(comment, models.Comment))

#def user_assert_can_post_comment(self, parent_post):
#def user_assert_can_delete_comment(self, comment = None):

#def user_assert_can_vote_for_post(
#def user_assert_can_revoke_old_vote(self, vote):

#def user_assert_can_flag_offensive(self):

#def user_assert_can_upload_file(request_user):
#def user_assert_can_post_question(self):
#def user_assert_can_post_answer(self):
#def user_assert_can_edit_post(self, post = None):
#def user_assert_can_delete_Post(self, post = None):
#def user_assert_can_close_question(self, question = None):
#def user_assert_can_retag_questions(self):

class VotePermissionAssertionTests(PermissionAssertionTestCase):
    """Tests permission for voting
    """
    def extraSetUp(self):
        self.min_rep_up = askbot_settings.MIN_REP_TO_VOTE_UP
        self.min_rep_down = askbot_settings.MIN_REP_TO_VOTE_DOWN
        self.other_user = self.create_other_user()

    def assert_cannot_vote(self, user = None, dir = None):
        assert(dir in ('up', 'down'))

        vote_func = self.get_vote_function(
                                        user = user, 
                                        dir = dir
                                    )

        self.assertRaises(
                exceptions.PermissionDenied,
                vote_func,
                self.question,
            )
        self.assertRaises(
                exceptions.PermissionDenied,
                vote_func,
                self.answer,
            )

    def prepare_data(self, status = 'a', rep = 1):
        self.question = self.post_question()
        self.answer = self.post_answer(question = self.question)
        self.other_user.reputation = rep
        self.other_user.set_status(status)

    def bad_user_cannot_vote(self, status = 'a', rep = 1, dir = 'up'):
        """dir - vote direction up/down
        rep - reputation
        """
        self.prepare_data(status = status)

        self.assert_cannot_vote(
                        user = self.other_user,
                        dir = dir
                    )

    def get_vote_function(self, dir = None, user = None):

        def vote_func(post):
            user.assert_can_vote_for_post(post = post, direction = dir)
        
        return vote_func


    def good_user_can_vote(self, user = None, dir = 'up'):

        if user is None:
            user = self.other_user

        vote_func = self.get_vote_function(dir = dir, user = user)

        vote_func(self.question)
        vote_func(self.answer)


    def test_blocked_user_cannot_vote(self):
        self.bad_user_cannot_vote(status = 'b')

    def test_suspended_user_cannot_vote(self):
        self.bad_user_cannot_vote(status = 's')

    def test_low_rep_user_cannot_upvote(self):
        self.bad_user_cannot_vote(dir = 'up')

    def test_low_rep_user_cannot_downvote(self):
        self.bad_user_cannot_vote(dir = 'down')

    def test_high_rep_user_can_upvote(self):
        self.prepare_data(rep = self.min_rep_up)
        self.good_user_can_vote(dir = 'up')

    def test_high_rep_user_can_downvote(self):
        self.prepare_data(rep = self.min_rep_down)
        self.good_user_can_vote(dir = 'down')

    def test_low_rep_admins_can_upvote_others(self):
        self.prepare_data()
        self.other_user.set_status('m')
        self.good_user_can_vote(dir = 'up')

    def test_low_rep_admins_can_downvote_others(self):
        self.prepare_data()
        self.other_user.set_status('m')
        self.good_user_can_vote(dir = 'down')

    def test_admins_cannot_upvote_self(self):
        self.prepare_data()
        self.user.set_status('m')
        self.assert_cannot_vote(
                user = self.user,
                dir = 'up'
            )

    def test_admins_cannot_downvote_self(self):
        self.prepare_data()
        self.user.set_status('m')
        self.assert_cannot_vote(
                user = self.user,
                dir = 'down'
            )

class UploadPermissionAssertionTests(PermissionAssertionTestCase):
    """Tests permissions for file uploads
    """

    def extraSetUp(self):
        self.min_rep = askbot_settings.MIN_REP_TO_UPLOAD_FILES

    def test_suspended_user_cannot_upload(self):
        self.user.set_status('s')
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.assert_can_upload_file
                )

    def test_blocked_user_cannot_upload(self):
        self.user.set_status('b')
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.assert_can_upload_file
                )
    def test_low_rep_user_cannot_upload(self):
        self.user.reputation = self.min_rep - 1
        self.assertRaises(
                    exceptions.PermissionDenied,
                    self.user.assert_can_upload_file
                )

    def test_high_rep_user_can_upload(self):
        self.user.reputation = self.min_rep
        try:
            self.user.assert_can_upload_file()
        except exceptions.PermissionDenied:
            self.fail('high rep user must be able to upload')

    def test_low_rep_moderator_can_upload(self):
        assert(self.user.reputation < self.min_rep)
        self.user.set_status('m')
        try:
            self.user.assert_can_upload_file()
        except exceptions.PermissionDenied:
            self.fail('high rep user must be able to upload')

    def test_low_rep_administrator_can_upload(self):
        assert(self.user.reputation < self.min_rep)
        self.user.is_superuser = True
        try:
            self.user.assert_can_upload_file()
        except exceptions.PermissionDenied:
            self.fail('high rep user must be able to upload')
