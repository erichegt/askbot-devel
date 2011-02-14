"""utility functions used by Askbot test cases
"""
from django.test import TestCase
from askbot import models

def create_user(
            username = None, 
            email = None, 
            notification_schedule = None,
            date_joined = None,
            status = 'a',
            reputation = 1
        ):
    """Creates a user and sets default update subscription
    settings"""
    user = models.User.objects.create_user(username, email)
    user.reputation = reputation
    if date_joined is not None:
        user.date_joined = date_joined
        user.save()
    user.set_status(status)
    if notification_schedule == None:
        notification_schedule = models.EmailFeedSetting.NO_EMAIL_SCHEDULE
        
    for feed_type, frequency in notification_schedule.items():
        feed = models.EmailFeedSetting(
                        feed_type = feed_type,
                        frequency = frequency,
                        subscriber = user
                    )
        feed.save()
    return user


class AskbotTestCase(TestCase):
    """adds some askbot-specific methods
    to django TestCase class
    """

    def create_user(
                self,
                username = 'user',
                email = None,
                notification_schedule = None,
                date_joined = None,
                status = 'a'
            ):
        """creates user with username, etc and
        makes the result accessible as

        self.<username>

        newly created user object is also returned
        """
        assert(username is not None)
        assert(not hasattr(self, username))

        if email is None:
            email = username + '@example.com'

        user_object = create_user(
                    username = username,
                    email = email,
                    notification_schedule = notification_schedule,
                    date_joined = date_joined,
                    status = status
                )

        setattr(self, username, user_object)

        return user_object

    def post_question(
                    self, 
                    user = None,
                    title = 'test question title',
                    body_text = 'test question body text',
                    tags = 'test',
                    wiki = False,
                    is_anonymous = False,
                    follow = False,
                    timestamp = None
                ):
        """posts and returns question on behalf
        of user. If user is not given, it will be self.user

        if follow is True, question is followed by the poster
        """

        if user is None:
            user = self.user

        question = user.post_question(
                            title = title,
                            body_text = body_text,
                            tags = tags,
                            wiki = wiki,
                            is_anonymous = is_anonymous,
                            timestamp = timestamp
                        )

        if follow:
            user.follow_question(question)

        return question

    def reload_object(self, obj):
        """reloads model object from the database
        """
        return obj.__class__.objects.get(id = obj.id)
        
    def post_answer(
                    self,
                    user = None,
                    question = None,
                    body_text = 'test answer text',
                    follow = False,
                    wiki = False,
                    timestamp = None
                ):

        if user is None:
            user = self.user
        return user.post_answer(
                        question = question,
                        body_text = body_text,
                        follow = follow,
                        wiki = wiki,
                        timestamp = timestamp
                    )

    def post_comment(
                self,
                user = None,
                parent_post = None,
                body_text = 'test comment text',
                timestamp = None
            ):
        """posts and returns a comment to parent post, uses 
        now timestamp if not given, dummy body_text 
        author is required
        """
        if user is None:
            user = self.user

        comment = user.post_comment(
                        parent_post = parent_post,
                        body_text = body_text,
                        timestamp = timestamp,
                    )

        return comment
